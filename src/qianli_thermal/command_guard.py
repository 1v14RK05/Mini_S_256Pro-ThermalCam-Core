# -*- coding: utf-8 -*-
"""Thread-safe command handle ownership guard.
Guardia de propiedad del handle de comandos entre hilos.

Prevents concurrent or re-entrant SDK calls from Python threads.
Evita llamadas concurrentes o reentrantes al SDK desde hilos de Python.
"""
from __future__ import annotations

from contextlib import contextmanager
from threading import RLock, get_ident
from typing import Iterator


class InvalidCommandSession(RuntimeError):
    """Raised on invalid handle state or cross-thread access."""


class CommandOwner:
    """Serializes read, batch calibration, ambient, and range operations on a single owner thread."""

    def __init__(self) -> None:
        self._creator = get_ident()
        self._lock = RLock()
        self._handle = 0
        self._state = "unopened"
        self._generation = 0
        self._active_reads = 0
        self._batch_active = False
        self._change_active = False
        self._range_changes = 0
        self._local_range_epoch = 0

    def _check_thread(self) -> None:
        if get_ident() != self._creator:
            raise InvalidCommandSession("Access outside the handle-owning thread")

    def register(self, handle: int) -> None:
        """Register an opened command handle."""
        with self._lock:
            self._check_thread()
            if self._state != "unopened" or not isinstance(handle, int) or handle <= 0:
                raise InvalidCommandSession("Duplicate or invalid initial handle")
            self._handle = handle
            self._generation += 1
            self._state = "active"

    @contextmanager
    def read_guard(self) -> Iterator[int]:
        """Acquire read-only permission on the command handle."""
        with self._lock:
            self._check_thread()
            if self._state != "active" or not self._handle:
                raise InvalidCommandSession("Session closed or uninitialized")
            if self._change_active or self._batch_active:
                raise InvalidCommandSession("Nested GET forbidden during range SET or batch read")
            self._active_reads += 1
            try:
                yield self._handle
            finally:
                self._active_reads -= 1

    @contextmanager
    def batch_guard(self) -> Iterator[int]:
        """Reserve exclusive access for a full calibration batch."""
        with self._lock:
            self._check_thread()
            if (
                self._state != "active"
                or not self._handle
                or self._active_reads
                or self._batch_active
                or self._change_active
            ):
                raise InvalidCommandSession("Handle busy; cannot start exclusive batch")
            self._batch_active = True
            self._active_reads += 1
            try:
                yield self._handle
            finally:
                self._active_reads -= 1
                self._batch_active = False

    @contextmanager
    def range_change_guard(self) -> Iterator[int]:
        """Serialize a LOW/HIGH range switch on the owner thread."""
        with self._lock:
            self._check_thread()
            if (
                self._state != "active"
                or not self._handle
                or self._active_reads
                or self._batch_active
                or self._change_active
            ):
                raise InvalidCommandSession("Handle busy; cannot switch range")
            self._range_changes += 1
            self._local_range_epoch += 1
            self._change_active = True
            self._active_reads += 1
            try:
                yield self._handle
            finally:
                self._active_reads -= 1
                self._change_active = False

    def invalidate_before_delete(self) -> None:
        """Must be called before ircmd_delete_handle."""
        with self._lock:
            self._check_thread()
            if self._active_reads or self._batch_active or self._change_active:
                raise InvalidCommandSession("Cannot release handle while an operation is active")
            if self._state == "active":
                self._state = "closed"
                self._generation += 1
                self._handle = 0

    def summary(self) -> dict:
        """Return safe status metadata (no handle pointers or sensor data)."""
        with self._lock:
            return {
                "state": self._state,
                "generation": self._generation,
                "active_reads": self._active_reads,
                "batch_active": self._batch_active,
                "change_active": self._change_active,
                "local_range_epoch": self._local_range_epoch,
                "range_changes_requested": self._range_changes,
            }

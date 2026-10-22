"""Finite stdout fixture, emitting only a requested bounded count of x bytes."""
import sys

count = int(sys.argv[1])
assert 0 <= count <= 65536
sys.stdout.buffer.write(b'x' * count)

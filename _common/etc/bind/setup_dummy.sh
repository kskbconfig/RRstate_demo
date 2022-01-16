#!/bin/sh
ip link add dn42-dummy type dummy || true
ip link set dn42-dummy up || true
ip addr add 10.127.111.233 dev dn42-dummy || true
ip addr add fd10:127:e00f:aca::233 dev dn42-dummy || true

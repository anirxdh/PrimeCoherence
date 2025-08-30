OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0],q[1];
rz(1.5708) q[2];
cx q[1],q[2];

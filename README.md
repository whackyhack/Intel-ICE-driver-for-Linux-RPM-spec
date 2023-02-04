# Intel-ICE-driver-for-Linux-RPM-spec
Improvement (or bug fix, depending on your view) on the RPM spec that comes
with Intel's ice Linux* Base Driver for the Intel(R) Ethernet 800 Series

The source is from a tar file provided under GPL 2.0 from
https://www.intel.com/content/www/us/en/download/19630/intel-network-adapter-driver-for-e810-series-devices-under-linux.html.
Specifically, this is based on Intel's version 1.10.1.2.2, although you can
apply the same patch to other versions at least in theory.  Part of Intel's
proprietary code is covered under BSD-3-Clause. (See ice/scripts/adqsetup/README.md.)

This project will only address the spec, although the entire text content of
the tar file is imported for context.  The improved spec is to be used with
Intel's original tar file.  Specifically, I am excluding proprietary machine
code (named ice-1.3.30.0.pkg under ddp/) included in the original tar because
it is excluded from any open source license.  As a result, even though Intel's
Linux code (as of version 1.10.1.2.2) is present, a tar file using this project
will NOT render a valid RPM.

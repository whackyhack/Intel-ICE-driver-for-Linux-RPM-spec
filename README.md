# Intel-ICE-driver-for-Linux-RPM-spec
Improvement (or bug fix, depending on your view) on the RPM spec that comes with Intel's ice Linux* Base Driver for the Intel(R) Ethernet 800 Series

The source is from a tar file provided under GPL 2 from https://www.intel.com/content/www/us/en/download/19630/intel-network-adapter-driver-for-e810-series-devices-under-linux.html.  Specifically, this is based on Intel's version 1.10.1.2.2, although you can apply the same patch to other versions at least in theory.

This project will only address the spec, although the entire text content of the tar file will be imported for context.  The improved spec is to be used with Intel's original tar file.  Specifically, I am excluding the machine code (named ice-1.3.30.0.pkg under ddp/) included in the original tar because it is unclear if GPL 2.0 specifically applies to those codes.  As a result, even though Intel's Linux code (as of version 1.10.1.2.2) is present, a tar file using this project will not render a valid RPM.


%define vendor_name ice
%if 0%{?ICE_VERSION:1}
%define ice_ver %{ICE_VERSION}
%else
%define ice_ver 1.10.1.2.2
%endif

#%%define _custom_pref tm
%if 0%{?_custom_pref:1}
Name: %{_custom_pref}-%{vendor_name}
%else
Name: %{vendor_name}
%endif
Summary: Intel(R) Ethernet Connection E800 Series Linux Driver
#%%define _custom_ver 1.0
%if 0%{?_custom_ver:1}
Version: %{ice_ver}_%{_custom_ver}
%else
%{echo:ERROR: Monotonously increasing <_custom_ver> is required.

Usage: rpmbuild --define '_custom_ver <your own incremental version>' \
       [--define '_custom_pref <your own package prefix>'] \
       [--define 'PACKAGER <your name> (<your E-mail)'] \
       [--define 'BUILD_KERNEL <target kernel release including platform>'] \
       [--define 'ICE_VERSION <Intel''s ice package version>'] \
       [--define 'AUX_VERSION <Intel''s internal version for auxiary bus>'] \
       -ba SPECS/ice_imp.spec
}
%endif
Release: 1
Source: %{vendor_name}-%{ice_ver}.tar.gz
Vendor: Intel Corporation
# Packager: Threatmetrix, Inc., a LexisNexisRisk company (yuan.liu@lexisnexisrisk.com)
%if 0%{?PACKAGER:1}
Packager: %{PACKAGER}
%else
%{error:Add --define 'PACKAGER <your name> (<your E-mail>)'}
%endif
License: GPLv2 and Redistributable
ExclusiveOS: linux
Group: System Environment/Kernel
Provides: %{name}
URL: http://support.intel.com
BuildRoot: %{_tmppath}/%{name}-%{ice_ver}-root
%global debug_package %{nil}
# macros for finding system files to update at install time (pci.ids, pcitable)
%define find() %(for f in %*; do if [ -e $f ]; then echo $f; break; fi; done)
%define _pciids   /usr/share/pci.ids        /usr/share/hwdata/pci.ids
%define _pcitable /usr/share/kudzu/pcitable /usr/share/hwdata/pcitable /dev/null
%define pciids    %find %{_pciids}
%define pcitable  %find %{_pcitable}

%if 0%{?BUILD_KERNEL:1}
%define kernel_ver %{BUILD_KERNEL}
%define check_aux_args_kernel -b %{BUILD_KERNEL} 
%else
%define kernel_ver %(uname -r)
%endif
%define kernel_rel %(sed 's/\.[^\.]*$//' <<<%{kernel_ver})
Requires: kernel = %{kernel_rel}, findutils, gawk, bash

%if 0%{?KSRC:1}
%define check_aux_args_ksrc -k %{KSRC}
%endif

%define check_aux_args %check_aux_args_kernel %check_aux_args_ksrc

%define need_aux_rpm %( [ -L /lib/modules/%kernel_ver/source ] && \
                  (rpm -q --whatprovides /lib/modules/%kernel_ver/source/include/linux/auxiliary_bus.h > /dev/null 2>&1 && echo 0 || echo 2) || \
                  (rpm -q --whatprovides /lib/modules/%kernel_ver/build/include/linux/auxiliary_bus.h > /dev/null 2>&1 && echo 0 || echo 2) )

%if (%need_aux_rpm == 2)
%define aux_name intel_auxiliary
%if 0%{?AUX_VERSION:1}
%define aux_ver %{AUX_VERSION}
%else
%define aux_ver 1.0.0
%endif
%if 0%{?_custom_pref:1}
%define aux_pkg %{_custom_pref}-%{aux_name}
%else
%define aux_pkg %{aux_name}
%endif
%define _aux_custom_ver %{aux_ver}_%{_custom_ver}
Requires: %{aux_pkg} = %{_aux_custom_ver}
%endif

# Hard code requirement because some platforms (incorrectly) auto-populate
# kernel_module_package_buildreqs
%define kernel_module_package_buildreqs kernel-devel = %{kernel_rel}

BuildRequires: make, gcc
BuildRequires: %kernel_module_package_buildreqs

%description
This package contains the Intel(R) Ethernet Connection E800 Series Linux Driver for kernel %{kernel_ver}.

%prep
%setup -n %{vendor_name}-%{ice_ver}
ln -s %{vendor_name}-%{ice_ver} ../%{name}-%{version}

%build
make -C src clean
make -C src

%install
%define req_aux %( [[ "%{vendor_name}" =~ ^(ice|ice_sw|ice_swx|iavf|i40e)$ ]] && echo 0 || echo 1 )

# install drivers that have auxiliary driver dependency
%if (%req_aux == 0)
make -C src INSTALL_MOD_PATH=%{buildroot} MANDIR=%{_mandir} modules_install_no_aux mandocs_install
# Remove modules files that we do not want to include
find %{buildroot}/lib/modules/ -name 'modules.*' -exec rm -f {} \;
cd %{buildroot}
find lib -name "ice.ko" -printf "/%p\n" \
	>%{_builddir}/%{name}-%{version}/file.list
%if (%need_aux_rpm == 2)
make -C %{_builddir}/%{name}-%{version}/src INSTALL_MOD_PATH=%{buildroot} auxiliary_install

find lib -path "*extern-symvers/intel_auxiliary.symvers" -printf "/%p\n" \
	>%{_builddir}/%{name}-%{version}/aux.list
find * -name "auxiliary_bus.h" -printf "/%p\n" \
	>>%{_builddir}/%{name}-%{version}/aux.list
%endif
if [ "$(%{_builddir}/%{name}-%{version}/scripts/./check_aux_bus %check_aux_args; echo $?)" == "2" ] ; then
	find lib -name "intel_auxiliary.ko" -printf "/%p\n" \
	>>%{_builddir}/%{name}-%{version}/file.list
fi

# install drivers that do not have auxiliary driver dependency
%else
make -C src INSTALL_MOD_PATH=%{buildroot} MANDIR=%{_mandir} modules_install mandocs_install
# Remove modules files that we do not want to include
find %{buildroot}/lib/modules/ -name 'modules.*' -exec rm -f {} \;
cd %{buildroot}
find lib -name "ice.ko" \
	-fprintf %{_builddir}/%{name}-%{version}/file.list "/%p\n"
%endif



%clean
rm -rf %{buildroot}

%files -f file.list
/lib/firmware/updates/intel/ice/ddp/ice-1.3.30.0.pkg
/lib/firmware/updates/intel/ice/ddp/ice.pkg
/lib/firmware/updates/intel/ice/ddp/LICENSE

%defattr(-,root,root)
%{_mandir}/man7/ice.7.gz
%doc COPYING
%doc README
%doc file.list
%doc pci.updates

%post
if [ -d /usr/local/share/%{name} ]; then
	rm -rf /usr/local/share/%{name}
fi
mkdir /usr/local/share/%{name}
cp --parents %{pciids} /usr/local/share/%{name}/
echo "original pci.ids saved in /usr/local/share/%{name}";
if [ "%{pcitable}" != "/dev/null" ]; then
	cp --parents %{pcitable} /usr/local/share/%{name}/
	echo "original pcitable saved in /usr/local/share/%{name}";
fi

LD="%{_docdir}/%{name}";
if [ -d %{_docdir}/%{name}-%{version} ]; then
	LD="%{_docdir}/%{name}-%{version}";
fi

#Yes, this really needs bash
bash -s %{pciids} \
	%{pcitable} \
	$LD/pci.updates \
	$LD/pci.ids.new \
	$LD/pcitable.new \
	%{name} \
<<"END"
#! /bin/bash
# Copyright (C) 2017 Intel Corporation
# For licensing information, see the file 'LICENSE' in the root folder
# $1 = system pci.ids file to update
# $2 = system pcitable file to update
# $3 = file with new entries in pci.ids file format
# $4 = pci.ids output file
# $5 = pcitable output file
# $6 = driver name for use in pcitable file

exec 3<$1
exec 4<$2
exec 5<$3
exec 6>$4
exec 7>$5
driver=$6
IFS=

# pattern matching strings
ID="[[:xdigit:]][[:xdigit:]][[:xdigit:]][[:xdigit:]]"
VEN="${ID}*"
DEV="	${ID}*"
SUB="		${ID}*"
TABLE_DEV="0x${ID}	0x${ID}	\"*"
TABLE_SUB="0x${ID}	0x${ID}	0x${ID}	0x${ID}	\"*"

line=
table_line=
ids_in=
table_in=
vendor=
device=
ids_device=
table_device=
subven=
ids_subven=
table_subven=
subdev=
ids_subdev=
table_subdev=
ven_str=
dev_str=
sub_str=

# force a sub-shell to fork with a new stdin
# this is needed if the shell is reading these instructions from stdin
while true
do
	# get the first line of each data file to jump start things
	exec 0<&3
	read -r ids_in
	if [ "$2" != "/dev/null" ];then
	exec 0<&4
	read -r table_in
	fi

	# outer loop reads lines from the updates file
	exec 0<&5
	while read -r line
	do
		# vendor entry
		if [[ $line == $VEN ]]
		then
			vendor=0x${line:0:4}
			ven_str=${line#${line:0:6}}
			# add entry to pci.ids
			exec 0<&3
			exec 1>&6
			while [[ $ids_in != $VEN ||
				 0x${ids_in:0:4} < $vendor ]]
			do
				echo "$ids_in"
				read -r ids_in
			done
			echo "$line"
			if [[ 0x${ids_in:0:4} == $vendor ]]
			then
				read -r ids_in
			fi

		# device entry
		elif [[ $line == $DEV ]]
		then
			device=`echo ${line:1:4} | tr "[:upper:]" "[:lower:]"`
			table_device=0x${line:1:4}
			dev_str=${line#${line:0:7}}
			ids_device=`echo ${ids_in:1:4} | tr "[:upper:]" "[:lower:]"`
			table_line="$vendor	$table_device	\"$driver\"	\"$ven_str|$dev_str\""
			# add entry to pci.ids
			exec 0<&3
			exec 1>&6
			while [[ $ids_in != $DEV ||
				 $ids_device < $device ]]
			do
				if [[ $ids_in == $VEN ]]
				then
					break
				fi
				if [[ $ids_device != ${ids_in:1:4} ]]
				then
					echo "${ids_in:0:1}$ids_device${ids_in#${ids_in:0:5}}"
				else
					echo "$ids_in"
				fi
				read -r ids_in
				ids_device=`echo ${ids_in:1:4} | tr "[:upper:]" "[:lower:]"`
			done
			if [[ $device != ${line:1:4} ]]
			then
				echo "${line:0:1}$device${line#${line:0:5}}"
			else
				echo "$line"
			fi
			if [[ $ids_device == $device ]]
			then
				read -r ids_in
			fi
			# add entry to pcitable
			if [ "$2" != "/dev/null" ];then
			exec 0<&4
			exec 1>&7
			while [[ $table_in != $TABLE_DEV ||
				 ${table_in:0:6} < $vendor ||
				 ( ${table_in:0:6} == $vendor &&
				   ${table_in:7:6} < $table_device ) ]]
			do
				echo "$table_in"
				read -r table_in
			done
			echo "$table_line"
			if [[ ${table_in:0:6} == $vendor &&
			      ${table_in:7:6} == $table_device ]]
			then
				read -r table_in
			fi
			fi
		# subsystem entry
		elif [[ $line == $SUB ]]
		then
			subven=`echo ${line:2:4} | tr "[:upper:]" "[:lower:]"`
			subdev=`echo ${line:7:4} | tr "[:upper:]" "[:lower:]"`
			table_subven=0x${line:2:4}
			table_subdev=0x${line:7:4}
			sub_str=${line#${line:0:13}}
			ids_subven=`echo ${ids_in:2:4} | tr "[:upper:]" "[:lower:]"`
			ids_subdev=`echo ${ids_in:7:4} | tr "[:upper:]" "[:lower:]"`
			table_line="$vendor	$table_device	$table_subven	$table_subdev	\"$driver\"	\"$ven_str|$sub_str\""
			# add entry to pci.ids
			exec 0<&3
			exec 1>&6
			while [[ $ids_in != $SUB ||
				 $ids_subven < $subven ||
				 ( $ids_subven == $subven && 
				   $ids_subdev < $subdev ) ]]
			do
				if [[ $ids_in == $VEN ||
				      $ids_in == $DEV ]]
				then
					break
				fi
				if [[ ! (${ids_in:2:4} == "1014" &&
					 ${ids_in:7:4} == "052C") ]]
				then
					if [[ $ids_subven != ${ids_in:2:4} || $ids_subdev != ${ids_in:7:4} ]]
					then
						echo "${ids_in:0:2}$ids_subven $ids_subdev${ids_in#${ids_in:0:11}}"
					else
						echo "$ids_in"
					fi
				fi
				read -r ids_in
				ids_subven=`echo ${ids_in:2:4} | tr "[:upper:]" "[:lower:]"`
				ids_subdev=`echo ${ids_in:7:4} | tr "[:upper:]" "[:lower:]"`
			done
			if [[ $subven != ${line:2:4} || $subdev != ${line:7:4} ]]
			then
				echo "${line:0:2}$subven $subdev${line#${line:0:11}}"
			else
				echo "$line"
			fi
			if [[ $ids_subven == $subven  &&
			      $ids_subdev == $subdev ]]
			then
				read -r ids_in
			fi
			# add entry to pcitable
			if [ "$2" != "/dev/null" ];then
			exec 0<&4
			exec 1>&7
			while [[ $table_in != $TABLE_SUB ||
				 ${table_in:14:6} < $table_subven ||
				 ( ${table_in:14:6} == $table_subven &&
				   ${table_in:21:6} < $table_subdev ) ]]
			do
				if [[ $table_in == $TABLE_DEV ]]
				then
					break
				fi
				if [[ ! (${table_in:14:6} == "0x1014" &&
					 ${table_in:21:6} == "0x052C") ]]
				then
					echo "$table_in"
				fi
				read -r table_in
			done
			echo "$table_line"
			if [[ ${table_in:14:6} == $table_subven &&
			      ${table_in:21:6} == $table_subdev ]]
			then
				read -r table_in
			fi
			fi
		fi

		exec 0<&5
	done

	# print the remainder of the original files
	exec 0<&3
	exec 1>&6
	echo "$ids_in"
	while read -r ids_in
	do
		echo "$ids_in"
	done

	if [ "$2" != "/dev/null" ];then
	exec 0>&4
	exec 1>&7
	echo "$table_in"
	while read -r table_in
	do
		echo "$table_in"
	done
	fi

	break
done <&5

exec 3<&-
exec 4<&-
exec 5<&-
exec 6>&-
exec 7>&-

END

mv -f $LD/pci.ids.new  %{pciids}
if [ "%{pcitable}" != "/dev/null" ]; then
	mv -f $LD/pcitable.new %{pcitable}
fi

echo "Updating modules.dep for %{kernel_ver}..."
uname -r | grep BOOT || /sbin/depmod %{kernel_ver} -a > /dev/null 2>&1 || true

if which dracut >/dev/null 2>&1; then
	echo "Updating initramfs-%{kernel_ver} with dracut..."
	if dracut --force --kver %{kernel_ver}; then
		echo "Successfully updated initramfs."
	else
		echo "Failed to update initramfs."
		echo "You must update your initramfs image for changes to take place."
		exit -1
	fi
elif which mkinitrd >/dev/null 2>&1; then
	echo "Updating initrd-%{kernel_ver} with mkinitrd..."
	if mkinitrd --image-version %{kernel_ver}; then
		echo "Successfully updated initrd."
	else
		echo "Failed to update initrd."
		echo "You must update your initrd image for changes to take place."
		exit -1
	fi
else
	echo "Unable to determine utility to update initrd image for %{kernel_ver}."
	echo "You must update your initrd manually for changes to take place."
	exit -1
fi

%preun
rm -rf /usr/local/share/%{name}

%postun
echo "Update modules.dep for %{kernel_ver}..."
uname -r | grep BOOT || /sbin/depmod -a %{kernel_ver} > /dev/null 2>&1 || true

if which dracut >/dev/null 2>&1; then
	echo "Updating initramfs-%{kernel_ver} with dracut..."
	if dracut --force --kver %{kernel_ver}; then
		echo "Successfully updated initramfs."
	else
		echo "Failed to update initramfs."
		echo "You must update your initramfs image for changes to take place."
		exit -1
	fi
elif which mkinitrd >/dev/null 2>&1; then
	echo "Updating initrd-%{kernel_ver} with mkinitrd..."
	if mkinitrd /boot/initrd-%{kernel_ver}.img %{kernel_ver}; then
		echo "Successfully updated initrd."
	else
		echo "Failed to update initrd."
		echo "You must update your initrd image for changes to take place."
		exit -1
	fi
else
	echo "Unable to determine utility to update initrd image for %{kernel_ver}."
	echo "You must update your initrd manually for changes to take place."
	exit -1
fi

%if (%need_aux_rpm == 2) && (%req_aux == 0)
%package -n %{aux_pkg}
Summary: Auxiliary bus driver (backport)
Version: %{_aux_custom_ver}
Requires: kernel-devel = %{kernel_rel}

%description -n %{aux_pkg}
The Auxiliary bus driver (intel_auxiliary.ko), backported from upstream, for use with kernel %{kernel_ver} which doesn't have auxiliary bus.

# The if is used to hide this whole section. This causes RPM to skip the build
# of the auxiliary subproject entirely.
%files -n %{aux_pkg} -f aux.list
%doc aux.list
%endif

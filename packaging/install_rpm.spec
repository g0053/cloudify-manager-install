%define __find_provides %{nil}
%define __find_requires %{nil}
%define _use_internal_dependency_generator 0

%define _source_payload w0.gzdio
%define _binary_payload w0.gzdio

Name:           cloudify-manager
Version:        %{CLOUDIFY_VERSION}
Release:        %{CLOUDIFY_PACKAGE_RELEASE}%{?dist}
Summary:        Cloudify Manager
Group:          Applications/Multimedia
License:        Apache 2.0
URL:            https://github.com/cloudify-cosmo/cloudify-manager-install
Vendor:         Cloudify Platform Ltd.
Packager:       Cloudify Platform Ltd.

BuildRequires:  createrepo


%description
Cloudify's REST Service.


%build

%install
mkdir %{buildroot}/opt
mkdir -p %{buildroot}/usr/bin
cp ${RPM_SOURCE_DIR}/etc %{buildroot}/etc -fr
cp ${RPM_SOURCE_DIR}/cloudify %{buildroot}/opt/cloudify -fr
cp ${RPM_SOURCE_DIR}/cfy_manager %{buildroot}/usr/bin/cfy_manager

/bin/createrepo %{buildroot}/opt/cloudify/sources
cp ${RPM_SOURCE_DIR}/packaging/localrepo /etc/yum.repos.d/Cloudify-Local.repo

%post
echo "
###########################################################################
Cloudify installer is ready!
To install Cloudify Manager, run:
cfy_manager install --private-ip <PRIVATE_IP> --public-ip <PUBLIC_IP>
(Use cfy_manager -h for a full list of options)

You can specify more installation settings in /etc/cloudify/config.yaml. If you
specify the public and private IP addresses in the config.yaml file, run:
cfy_manager install
###########################################################################
"

%files
/etc/yum.repos.d/Cloudify-Local.repo
/usr/bin/cfy_manager
/etc/cloudify/config.yaml
/opt/cloudify

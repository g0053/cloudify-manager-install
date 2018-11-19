Name:           cloudify-manager
Version:        %{CLOUDIFY_VERSION}
Release:        %{CLOUDIFY_PACKAGE_RELEASE}%{?dist}
Summary:        Cloudify Manager
Group:          Applications/Multimedia
License:        Apache 2.0
URL:            https://github.com/cloudify-cosmo/cloudify-manager
Vendor:         Cloudify Platform Ltd.
Packager:       Cloudify Platform Ltd.

Requires: cloudify-management-worker
Requires: cloudify-rest-service
Requires: cloudify-amqp-influx
Requires: cloudify
Requires: jre
Requires: cloudify-manager-ip-setter
Requires: libxslt
Requires: postgresql95
Requires: postgresql95-server
Requires: postgresql95-contrib
Requires: python-psycopg2
Requires: cloudify-rabbitmq
Requires: cloudify-agents

%description
Cloudify Manager

%build
%install

%files

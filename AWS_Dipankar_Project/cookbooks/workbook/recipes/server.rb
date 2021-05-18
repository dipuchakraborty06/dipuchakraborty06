#
# Cookbook:: workbook
# Recipe:: server
# Maintainer:: Dipankar Chakraborty
#
# Copyright:: 2021, The Authors, All Rights Reserved.
group "web-admin" do
    action :create
    group_name "web-admin"
    gid "1001"
end
user "web-admin" do
    username "web-admin"
    comment "Apache httpd service user"
    uid "1001"
    gid "1001"
    home "/home/web-admin"
    shell "/bin/bash"
end
package "httpd" do
    action :install
end
service "httpd" do
    action [:enable, :start]
end


Vagrant.configure("2") do |config|
  config.vm.box = "trusty64"
  config.vm.box_url = "https://vagrantcloud.com/ubuntu/trusty64/version/1/provider/virtualbox.box"
  config.vm.hostname = "openspending"

  config.cache.auto_detect = true

  config.vm.network :forwarded_port, guest: 5000, host: 5000
  config.vm.network :forwarded_port, guest: 8080, host: 8080
  config.vm.network :forwarded_port, guest: 8983, host: 8983

  config.vm.provider :virtualbox do |vb|
  #   # Use VBoxManage to customize the VM. For example to change memory:
  #   vb.customize ["modifyvm", :id, "--memory", "2048"]
	  vb.memory = 1024
  end

  config.vm.provision :shell, :privileged => false, :path => 'bin/vagrant_deploy'
end

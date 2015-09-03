.PHONY: all
all: autocluster

.PHONY: umbrella
umbrella:
	git remote rename origin strato
	git remote add origin https://github.com/rabbitmq/rabbitmq-public-umbrella.git
	make co
	make BRANCH=rabbitmq_v3_5_1 up_c

.PHONY: autocluster
autocluster: umbrella
	git clone https://github.com/Stratoscale/rabbitmq-autocluster.git rabbitmq_autocluster_consul
	cd rabbitmq_autocluster_consul && git checkout 09b32bd31ce1bc3352912e3ec3005695bfce33b9
	make -C rabbitmq_autocluster_consul

.PHONY: submit
submit:
	solvent submitproduct autocluster rabbitmq_autocluster_consul/dist

.PHONY: approve
approve:
	solvent approve --product=autocluster

.PHONY: prepareForCleanBuild
prepareForCleanBuild:
	sudo yum install erlang --assumeyes

.PHONY: clean
clean:
	sudo rm -fr build

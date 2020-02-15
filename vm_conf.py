import paramiko
import sys
import os
import re

def put_file(machinename,port ,username, password, path):


    def vm_mode(ssh, id):
        command = "vim-cmd vmsvc/get.guest " \
                + vm_id + " | awk \'/guestState|guestOperations/ {print $0}\'"
        stdin, stdout, stderr = ssh.exec_command(command)
        out = stdout.read().decode('ascii').strip()
        return out.split(',')[0].strip(), out.split(',')[1].strip()


    def vm_mode_check(vm_status):
        if vm_status == "\"running\"":
            return True
        elif vm_status == "\"notRunning\"":
            return False


    def vm_off(ssh, id):
        command = "vim-cmd vmsvc/power.off " + vm_id
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print(stdout.read().decode('ascii').strip(), id)



    def vm_on(ssh, id):
        command = "vim-cmd vmsvc/power.on " + vm_id
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print(stdout.read().decode('ascii').strip(), id)


    def change_config(ssh, vm_path):
        sftp = ssh.open_sftp()
        full_path = "/vmfs/volumes/" + vm_path
        pattern = re.compile('[\w]*\.network[\w\s]*=[\s](\"(\w{1,})\")')
        f1 = sftp.open(full_path, 'r')
        f2 = sftp.open("myp.txt", 'w')
        idx = 1
        for line in f1:
        	if re.match(pattern, line):
        		idx+=1
        		old_value = line.split('= ')[1]
        		new_value = str("\"" + sys.argv[idx] + "\"" + "\n")
        		f2.write(line.replace(old_value, new_value))
        	else:
        		f2.write(line)
        f1.close()
        f2.close()

        f1 = sftp.open(full_path, 'w')
        f2 = sftp.open("myp.txt", 'r')
        for line in f2:
            f1.write(line)
        f1.close()
        f2.close()
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("Configuration change has perfomred.\n")


    def vm_reload(ssh, vm_path, id):
        change_config(ssh, vm_path)
        command = "vim-cmd vmsvc/reload  " + id
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("Reload has perfomred.\n")
        vm_on(ssh, id)


    def vm_mode_change(ssh, st, id, path):
        if vm_mode_check(st):
            vm_off(ssh, id)
            vm_reload(ssh, path, id)
            print("First VM was on, we turned it off, then reload performed!\n")
        else:
            vm_reload(ssh, path, id)
            print("First VM was off, so reload performed!\n")


    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(machinename, port, username, password)
    command = "vim-cmd vmsvc/getallvms | grep " \
            + str(sys.argv[1])
    stdin, stdout, stderr = ssh.exec_command(command)
    pattern = \
    re.compile(\
        '(\d{1,}\s*)(\w*\s*\[)(\w*)(\])(\s?)([\w*\s?]+)(/?)([\w*\s?]+\.\w{3})'
              )
    s = stdout.read().decode('ascii')
    if re.match(pattern, s):
        print(re.match(pattern,s).group(3) + "/" + \
              re.match(pattern,s).group(6) + \
              re.match(pattern,s).group(7) + \
              re.match(pattern,s).group(8) )
        vm_id = re.match(pattern,s).group(1)
        path = re.match(pattern,s).group(3) + "/" + \
              re.match(pattern,s).group(6) + \
              re.match(pattern,s).group(7) + \
              re.match(pattern,s).group(8)

    # getting the VM status before any action
    vm_st, vm_op = vm_mode(ssh, vm_id)

    # changing the configuration
    vm_mode_change(ssh, vm_st.split(' = ')[1], vm_id, path)
    # vm_st, vm_op = vm_mode(ssh, vm_id)
    # print(vm_st, vm_op)
    ssh.close()

put_file('1.2.3.4', 22, 'root', 'mypassmypass', sys.argv[1])

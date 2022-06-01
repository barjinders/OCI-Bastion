from os import system
import oci
import time
import logging 
import asyncio
import sys
import json

#Logging basic config
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

#Open user inputs file
f = open('/Users/barjindersingh/Documents/OCI-Code/DNS/userInputsBastion.JSON')

# parse the JSON file
try:
    data = json.load(f)
except json.decoder.JSONDecodeError:
    raise("Invalid user inputs JSON")

config = oci.config.from_file("~/.oci/configp", "DEFAULT")

# Initialize service client with default config file
bastion_client = oci.bastion.BastionClient(config)

#Gloabl control variables
WaitRefresh = 15
sessionCount = 1
maxSessionCount = 4

#Ceate a bastion session and wait for it to be active. 
def create_bastion_session(userInputs):
    try:
        create_session_response = bastion_client.create_session(create_session_details=oci.bastion.models.CreateSessionDetails(
                bastion_id=userInputs["bastionID"],
                target_resource_details=oci.bastion.models.CreateManagedSshSessionTargetResourceDetails(
                    session_type=userInputs["sessionType"],
                    target_resource_operating_system_user_name=userInputs["target_resource_operating_system_user_name"],
                    target_resource_id=userInputs["target_resource_id"],
                    target_resource_port=userInputs["target_resource_port"],
                    target_resource_private_ip_address= userInputs["target_resource_private_ip_address"]
                    ),
                key_details=oci.bastion.models.PublicKeyDetails(
                    public_key_content=userInputs["public_key_content"]
                    ),
                display_name=userInputs["display_name"],
                key_type=userInputs["key_type"],
                session_ttl_in_seconds=userInputs["session_ttl_in_seconds"])
                )
        
        get_session_response = bastion_client.get_session(session_id= create_session_response.data.id)
    except:
        raise ("Oops! Error creating the session with the supplied parameters")
    activeSession = False
    count = 0
    maxCount = 15
    try:
        while activeSession == False and count < maxCount:
            get_session_response = bastion_client.get_session(session_id= create_session_response.data.id)
            if (get_session_response.data.lifecycle_state == "ACTIVE" ):
                logging.info("Session has been created and is ACTIVE")
                activeSession == True
                break
            else:
                logging.info("Waiting for session state to be active. Current State .."+ str(get_session_response.data.lifecycle_state))
                time.sleep(WaitRefresh)
                count = count + 1
    except:
        logging.exception ("Oops! Error getting the session with the session ID")

    return get_session_response.data

#Get the ssh command to run on the shell. 
def getCommand(session,userInputs):
    sessionCommand = session.ssh_metadata["command"]
    cmd = sessionCommand.replace("<privateKey>",userInputs["privateKey"])
    cmd = cmd.replace("<localPort>",userInputs["localPort"])
    return cmd

#Run the command on the shell. 
def runBastionCmd (sessionCount,maxSessionCount,userInputs):
    if sessionCount > maxSessionCount:
        sys.exit( "Maximum Sessions Reached!")
    session = create_bastion_session(userInputs)
    cmd = getCommand(session,userInputs)
    ttl = session.session_ttl_in_seconds
    #print("TTL of the session is : "+ str(ttl))
    print("Next session will be created after "+ str(ttl)+ " seconds. Taking a nap till then....")
    print("Please connect to OCI Machine. Bastion session is active.")
    asyncio.run(run(cmd))
    wait_for_session_deletion(session.id)
    #print("Session Details: "+ str(session))
    #time.sleep(ttl+60)
    return session

#Run async command and wait for the output. 
async def run(cmd: str):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logging.error(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        logging.info(f'[stdout]\n{stdout.decode()}')
    if stderr:
        logging.error(f'[stderr]\n{stderr.decode()}')

#Check the status of previous session and wait for the session to deleted. 
def wait_for_session_deletion(sessionID):
    session_deletion = False
    tries = 0
    maxTries = 20
    while session_deletion == False and tries < maxTries:
        get_session_response = bastion_client.get_session(session_id= sessionID)
        if (get_session_response.data.lifecycle_state != "DELETED" ):
            print("Previous session still active. Program will take a nap and check back again. Current status is  "+ str(get_session_response.data.lifecycle_state))
            print("Deleting the session..............")
            delete_session_response = bastion_client.delete_session(session_id=sessionID)
            print(delete_session_response.headers)
            time.sleep(WaitRefresh)
            tries = tries + 1
        else: 
            print("The previous session has been deleted")
            session_deletion = True
            break


#Run a while loop to create sessions till max sessions are reached. 
while sessionCount <= maxSessionCount: 
    try:
        print("************************************ Session Number: "+ str(sessionCount)+ " .Maximum Sessions allowed :"+ str(maxSessionCount)+" ************************************\n")
        ses =  runBastionCmd(sessionCount,maxSessionCount,data)
        sessionCount = sessionCount + 1 
    except KeyboardInterrupt:
        logging.error('Keyboard Interrupt user pressed ctrl-c button.')
        sys.exit(1)
    except:
        sessionCount = sessionCount + 1 
        logging.exception ("Session ended or unable to connect")
        if(sessionCount>maxSessionCount):
            print("Maximum session reached")
            sys.exit(1)
    else:
        logging.error('No errors, Session expired or deleted')
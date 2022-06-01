# OCI-Bastion
OCI Bastion Session Python SDK
The script creates a bastion session as per the user inputs. Once the session ends, it will create a new session and keep the user connected. 

User Inputs:
"bastionID": OCID OF BASTION SERVICE,
"sessionType": PORT_FORWARDING /MANAGED SSH,
"target_resource_operating_system_user_name": USER NAME OF THE JUMPHOST,
"target_resource_id": OCID OF JUMP HOST,
"target_resource_port": 3389 [RDP PORT],
"target_resource_private_ip_address": "TARGET JUMPHOST IP ADDRESS,
"public_key_content": SSH PUBLIC KEY,
"display_name": SESSION NAME,
"key_type": "PUB",
"session_ttl_in_seconds": SESSION TTL . MINIMUM 1800,
"privateKey": Private Key Location>,
"localPort": LOCAL PORT FOR FORWARDING,
"maxSessionCount":MAXIMUM BASTION SESSIONS TO BE CREATED IN ONE RUN. A VALUE OF 3 MEANS, ONCE THE CURRENT SESSION EXPIRES IT WILL CREATE 2 MORE SESSIONS. 

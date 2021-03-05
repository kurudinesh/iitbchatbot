import rsa

# generate public and private keys with
# rsa.newkeys method,this method accepts
# key length as its parameter
# key length should be atleast 16
publicKey = None
def getprivatekey():
    global publicKey
    publicKey, privatekey = rsa.newkeys(256)
    return privatekey.save_pkcs1().decode('utf-8')

def resetpubkey():
    global publicKey
    publicKey = None
    return "public set to empty"
# print(publicKey)
# print(privateKey)

# Save private and pub key
# with open('privatekey.priv','w+') as f:
#     f.write(privateKey.save_pkcs1().decode('utf-8'))
#
# with open('publickey.pub','w+') as f:
#     f.write(publicKey.save_pkcs1().decode('utf-8'))

# this is the string that we will be encrypting
# message = "hello geeks"

# rsa.encrypt method is used to encrypt
# string with public key string should be
# encode to byte string before encryption
# with encode method
def encryptmsg(message):
    if publicKey is not None:
        return rsa.encrypt(str(message).encode(),
						publicKey)
    return None

# print("original string: ", message)
# print("encrypted string: ", encMessage)

# the encrypted message can be decrypted
# with ras.decrypt method and private key
# decrypt method returns encoded byte string,
# use decode method to convert it to string
# public key cannot be used for decryption
def decryptmsg(key,encMessage):

    # with open('privatekey.priv','r') as f:
    #     key = f.read()

    privateKey = rsa.PrivateKey.load_pkcs1(key)


    decMessage = rsa.decrypt(encMessage, privateKey).decode()

    # print("decrypted string: ", decMessage)
    return decMessage

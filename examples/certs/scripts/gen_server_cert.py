#!/usr/bin/env python3

import OpenSSL
import OpenSSL.crypto

ca_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
        open("rootCA.crt").read())
ca_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM,
        open("rootCA.key").read())

key = OpenSSL.crypto.PKey()
key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

cert = OpenSSL.crypto.X509()
cert.set_version(3)
cert.set_serial_number(1)
cert.get_subject().CN = "reflectrpc"
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(10*365*24*60*60)
cert.set_issuer(ca_cert.get_subject())
cert.set_pubkey(key)
cert.sign(ca_key, "sha256")

f = open("server.crt", "wb")
f.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
f.close()

f = open("server.key", "wb")
f.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
f.close()

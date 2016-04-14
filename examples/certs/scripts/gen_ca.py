#!/usr/bin/env python3

import OpenSSL

key = OpenSSL.crypto.PKey()
key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

ca = OpenSSL.crypto.X509()
ca.set_version(3)
ca.set_serial_number(1)
ca.get_subject().CN = "MyCA"
ca.gmtime_adj_notBefore(0)
ca.gmtime_adj_notAfter(10*365*24*60*60)
ca.set_issuer(ca.get_subject())
ca.set_pubkey(key)
ca.add_extensions([
  OpenSSL.crypto.X509Extension("basicConstraints".encode("ASCII"), True,
                               "CA:TRUE, pathlen:0".encode("ASCII")),
  OpenSSL.crypto.X509Extension("keyUsage".encode("ASCII"), True,
                               "keyCertSign, cRLSign".encode("ASCII")),
  OpenSSL.crypto.X509Extension("subjectKeyIdentifier".encode("ASCII"), False, "hash".encode("ASCII"),
                               subject=ca),
  ])
ca.sign(key, "sha256")

cert_file = open("rootCA.crt", "wb")
cert_file.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, ca))
cert_file.close()

cert_file = open("rootCA.key", "wb")
cert_file.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
cert_file.close()

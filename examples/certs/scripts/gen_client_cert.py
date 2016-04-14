#!/usr/bin/env python3

import OpenSSL
import OpenSSL.crypto

def gen_cert_request(cname):
    pkey = OpenSSL.crypto.PKey()
    pkey.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

    req = OpenSSL.crypto.X509Req()
    req.get_subject().CN = cname
    req.set_pubkey(pkey)
    req.sign(pkey, 'sha512')

    req_file = OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)
    key_file = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey)

    return req_file, key_file

def sign_cert_request(ca_cert, ca_key, cert_request, serial):
    req = OpenSSL.crypto.load_certificate_request(OpenSSL.crypto.FILETYPE_PEM,
                                              cert_request)

    cert = OpenSSL.crypto.X509()
    cert.set_subject(req.get_subject())
    cert.set_serial_number(1)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(ca_cert.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(ca_key, "sha256")

    cert_file = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM,
            cert)

    return cert_file

req, private_key = gen_cert_request("example-username")

with open('rootCA.crt', 'rb') as f:
        ca_cert_content=f.read()

ca_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
                                          ca_cert_content)

with open('rootCA.key', 'rb') as f:
        ca_key_content=f.read()

ca_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                        ca_key_content)

cert = sign_cert_request(ca_cert, ca_key, req, 1)

# write the cert and key to disk
with open('client.crt', 'wb') as f:
        f.write(cert)

with open('client.key', 'wb') as f:
        f.write(private_key)

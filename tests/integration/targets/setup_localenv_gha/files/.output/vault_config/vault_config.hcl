listener "tcp" {
  tls_key_file = "/vault/config/key.pem"
  tls_cert_file = "/vault/config/cert.pem"
  tls_disable  = false
  address = "vault:8300"
}

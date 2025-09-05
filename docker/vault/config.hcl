ui=true
# local only convenience
disable_mlock = true

listener "tcp" {
    address = "0.0.0.0:8200"
    tls_disable = 1
}

# Simple file storage for local/dev persistence (switch to raft in team setup)
storage "file" {
    path = "/vault/file"
}

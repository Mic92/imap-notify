with import <nixpkgs> {};
python3.pkgs.buildPythonApplication {
  name = "imap-notify";
  src = ./.;
}

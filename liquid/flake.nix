{
  description = "c dev environment";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pname = "c dev environment";
        pkgs = nixpkgs.legacyPackages."${system}";
      in
        rec {
          inherit pname;

          # `nix develop`
          devShell = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [
              cmake
              pkg-config
            ];

            LD_LIBRARY_PATH = with pkgs; lib.makeLibraryPath [
              stdenv.cc.cc.lib
            ];

            shellHook = ''
              export LD_LIBRARY_PATH=../liquid-dsp/build:$LD_LIBRARY_PATH
              '';
          };
        }
    );
}
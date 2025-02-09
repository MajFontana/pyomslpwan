{
  description = "python dev environment";

  # to activate, type `nix develop` while in the repo dir or a subdir.
  # or use direnv to automatically do so (see .envrc)
  # for best results, don't have a global python installed.  mixing python
  # versions can make for venv problems.

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pname = "python dev environment";
        pkgs = nixpkgs.legacyPackages."${system}";
        venvDir = ".venv";
      in
        rec {
          inherit pname;

          # `nix develop`
          devShell = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [
              python3Packages.python
              python3Packages.python-lsp-server
              python3Packages.autopep8

              python3Packages.tkinter

              #https://discourse.nixos.org/t/python-matplotlib-cant-show-plot-in-nixos/52562
              pkgs.glib
              pkgs.zlib
              pkgs.libGL
              pkgs.fontconfig
              pkgs.xorg.libX11
              pkgs.libxkbcommon
              pkgs.freetype
              pkgs.dbus

              liquid-dsp
              cmake
              pkg-config
            ];

            buildInputs = with pkgs; [
              liquid-dsp
            ];

            LD_LIBRARY_PATH = with pkgs; lib.makeLibraryPath [
              stdenv.cc.cc.lib
              zlib
            ];

            shellHook = ''
                # create a virtualenv if there isn't one.

                # DOESN'T install deps for the python app.  Do that once `nix develop` runs with
                # $ cd src
                # $ pip install -r ./requirements.txt

                if [ -d "${venvDir}" ]; then
                  echo "Skipping venv creation, '${venvDir}' already exists"
                else
                  echo "Creating new venv environment in path: '${venvDir}'"
                  # Note that the module venv was only introduced in python 3, so for 2.7
                  # this needs to be replaced with a call to virtualenv
                  python -m venv "${venvDir}"
                  # unescape to attempt use
                  # \$\{pythonPackages.python.interpreter\} -m venv "${venvDir}"
                fi

                # activate our virtual env.
                source "${venvDir}/bin/activate"
              '';
          };
        }
    );
}
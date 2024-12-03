{pkgs ? import <nixpkgs> {}}:

let
  overlay = final: prev: {
    python3 = prev.python3.override {

      packageOverrides = python-final: python-prev: {

        /*RsWaveform =
          let
            pname = "RsWaveform";
            version = "0.3.0";
          in
            python-prev.buildPythonPackage {
            inherit pname version;
            src = prev.fetchPypi {
              inherit version;
              pname = "rswaveform";
              hash = "sha256-NdkgLk9ZFj1PJF47LifLfnxdHrqDbczgHpEyG2hQhHs=";
            };
            doCheck = false;
            format = "wheel";
          };*/

        /*aesonSrc = python-super.twisted.overrideAttrs (oldAttrs: {
          src = prev.fetchFromGitHub {
            owner = "obsidiansystems";
            repo = "aeson-gadt-th";
            rev = "ed573c2cccf54d72aa6279026752a3fecf9c1383";
            sha256 = "08q6rnz7w9pn76jkrafig6f50yd0f77z48rk2z5iyyl2jbhcbhx3";
          };
        });*/

      };
    };
  };
  pkgs' = pkgs.extend overlay;
in
  pkgs'.mkShell {
    buildInputs = [
      (pkgs'.python3.withPackages (ps: with ps; [
        matplotlib
        pyqt6

        #numpy
        #bitstring
        #pyzmq
        #numba
        #streamz
        #RsWaveform
        #twisted

        tkinter #https://stackoverflow.com/questions/9054718/matplotlib-doesnt-display-graph-in-virtualenv
      ]))

      #pkgs'.gcc

      #https://discourse.nixos.org/t/python-matplotlib-cant-show-plot-in-nixos/52562
      pkgs.glib
      pkgs.zlib
      pkgs.libGL
      pkgs.fontconfig
      pkgs.xorg.libX11
      pkgs.libxkbcommon
      pkgs.freetype
      pkgs.dbus

    ];

    LD_LIBRARY_PATH = with pkgs; lib.makeLibraryPath [
      stdenv.cc.cc.lib
      zlib
    ];

    shellHook = ". .venv/bin/activate";

  }
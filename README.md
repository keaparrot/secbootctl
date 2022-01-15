# secbootctl - Secure Boot Helper

[![CI](https://github.com/keaparrot/secbootctl/actions/workflows/CI.yaml/badge.svg)](https://github.com/keaparrot/secbootctl/actions/workflows/CI.yaml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/keaparrot-badge/9fd0dadcb588aa4fbceac2609331623f/raw/secbootctl-coverage.json)](https://github.com/keaparrot/secbootctl/actions/workflows/CI.yaml)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md)

secbootctl is designed to simplify the process of using UEFI Secure Boot with
your own custom keys under Linux. It helps to sign all files in the boot chain,
like kernel and initramfs images, by creating so called unified kernel images
that will be signed and installed on the EFI system partition (ESP). Furthermore
it can be used to manage the bootloader systemd-boot. Used together with your
distributions package manager the whole process can be automated in case of boot
relevant package updates.

## Table of contents

- [About the project](https://github.com/keaparrot/secbootctl#about-the-project)
- [Features](https://github.com/keaparrot/secbootctl#features)
- [Roadmap](https://github.com/keaparrot/secbootctl#roadmap)
- [Getting started](https://github.com/keaparrot/secbootctl#getting-started)
    - [Requirements ](https://github.com/keaparrot/secbootctl#requirements)
    - [Installation ](https://github.com/keaparrot/secbootctl#installation)
    - [Usage](https://github.com/keaparrot/secbootctl#usage)
    - [Configuration](https://github.com/keaparrot/secbootctl#configuration)
    - [Package manager integration](https://github.com/keaparrot/secbootctl#package-manager-integration)
- [Limitations ](https://github.com/keaparrot/secbootctl#limitations)
- [FAQ](https://github.com/keaparrot/secbootctl#faq)
- [Related projects](https://github.com/keaparrot/secbootctl#related-projects)
- [License](https://github.com/keaparrot/secbootctl#license)

## About the project

Some day I brainstormed about how to lightweight and secure my boot process. I
decided to use UEFI Secure Boot but get rid of the preinstalled Microsoft keys
and instead use my own custom keys. Besides, as I'm not doing any fancy boot
stuff and have systemd installed anyway, I decided to use systemd-boot in favor
of grub as bootloader.

To be able to use Secure Boot with my own keys, I have to sign the bootloader as
well as create and sign unified kernel images and copy them on the ESP. It can
become really cumbersome to do this manually on every kernel, initramfs,
microcode or bootloader update. Thus I searched if someone already developed a
tool that helps with it but didn't find anything that fully suited my needs. As
I'm using Arch Linux as well as Xubuntu I looked for a solution that was
configurable in a way that allows me to use it under both distributions out of
the box. In the end I started to write a python script myself. Maybe the script
is useful for someone else with similar requirements. That's why I
cleaned up the code, wrote some tests and finally
released it as open source under the project name secbootctl.

## Features

Below a list of what you can do with secbootctl:

- manage bootloader
    - install, update and remove bootloader on the ESP
    - sign and verify signature of bootloader files
    - print bootloader status
    - configure bootloader menu
    - supported bootloaders:
        - systemd-boot
- manage kernels
    - unify kernel, initramfs and optionally microcode images (so-called unified
      kernel images)
    - install, update and remove unified kernel images on the ESP
    - sign and verify signature of unified kernel images
- sign and verify signature of single files
- list signing status of all files on the ESP
- customize configuration via configuration file
- package manager integration for automation
    - supported package managers:
        - pacman (Arch Linux)

## Roadmap

Features & ideas that might be implemented in any future releases:

- key generation
- key enrollment
- key backup
- cmdline setting via configuration file
- support of using keys stored on a security token (e.g. Yubikey)
  via [PKCS#11-API](https://en.wikipedia.org/wiki/PKCS_11)
- support of non-bootloader usage (direct booting via UEFI firmware itself)
- support for integration with other package managers (probably starting with
  apt because besides Arch Linux I regularly use Xubuntu)

## Getting started

Learn how to install and use secbootctl to get started.

### Requirements

The following dependencies are required:

- [binutils](https://www.gnu.org/software/binutils/)
- [python](https://www.python.org/) (tested with >= v3.9)
- [sbsigntools](https://git.kernel.org/pub/scm/linux/kernel/git/jejb/sbsigntools.git/about/)
- [systemd-boot (systemd)](https://github.com/systemd/systemd)

All listed dependencies are available in the main repositories of Arch Linux,
Debian and Ubuntu (I just checked distributions I usually use myself).

Currently key generation and key enrollment are not supported (but planned - see
Roadmap). So you are required to generate your own custom Secure Boot keys and
enroll them on your own beforehand 
(see [related resources](https://github.com/keaparrot/secbootctl#related-resources)).

### Installation

To install secbootctl follow the steps below:

**Step 1:** Download the lastest release. You can either download it manually in
your web browser on the
[latest release page](https://github.com/keaparrot/secbootctl/releases/latest) 
or do it in your terminal on the command-line. In both cases download the 
following files:

- `secbootctl-{version}.tar.gz`
- `secbootctl-{version}.tar.gz.asc`

Example how to do it on the command-line with
[wget](https://www.gnu.org/software/wget/):

```
release_version=$(wget -qO - https://api.github.com/repos/keaparrot/secbootctl/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
wget "https://github.com/keaparrot/secbootctl/releases/download/${release_version}/secbootctl-${release_version}.tar.gz"
wget "https://github.com/keaparrot/secbootctl/releases/download/${release_version}/secbootctl-${release_version}.tar.gz.asc"
```

**Step 2:** For security reasons it is highly recommended to verify that the
signature of the downloaded archive file is valid:

```
gpg --import <(wget -qO - https://github.com/keaparrot.gpg)
gpg --with-fingerprint --verify secbootctl-${release_version}.tar.gz.asc secbootctl-${release_version}.tar.gz
```

**Step 3:** Unpack the downloaded and verified archive file and execute
the `install.py` script:

```
tar -xvzf secbootctl-${release_version}.tar.gz
cd secbootctl
chmod +x install.sh
sudo ./install.py
cd ..
rm -R secbootctl
```

Steps done by the `install.py` script:

- zips current working directory with pythons
  [zipapp](https://docs.python.org/3/library/zipapp.html) and copies the zip
  file to `/usr/local/bin/secbootctl` with permissions `root:root:755`
- creates following directory structure (including config and hook files):

```
/etc/ 
└── secbootctl/ (root:root:755)
   ├── hooks/ (root:root:755)
   ├── keys/ (root:root:700)
   └── secbootctl.conf (root:root:644)
```

**Step 4:** Copy your own custom Secure Boot keys manually
into `/etc/secbootctl/keys` with permissions of `root:root:400`.

**Step 5:** Check the default configuration in `/etc/secbootctl/secbootctl.conf`
and adjust it if necessary.

**Step 6 (optional)**: Last but not least it's advertised that you create the
file `/etc/kernel/cmdline` and add your custom kernel cmdline that will be used
when booting (will be embedded into the unified kernel image). If this file is
not present then `/proc/cmdline` will be used as fallback.

### Usage

```
~$ secbootctl 
secbootctl v0.1 - Secure Boot Helper

Usage: secbootctl [-h] [-V] [command] ...

Commands:
  bootloader:install      install bootloader (systemd-boot)
  bootloader:update       update bootloader (systemd-boot)
  bootloader:remove       remove bootloader (systemd-boot)
  bootloader:status       show bootloader status (systemd-boot)
  bootloader:update-menu  update bootloader menu
  kernel:install          install given or default kernel
  kernel:remove           remove given or default kernel
  config:list             list current config
  file:list               list files on ESP with signing status
  file:sign               sign given file
  file:verify             verify signature of given file
  pmi:install             install package manager hook
  pmi:remove              remove package manager hook
  pmi:hook-callback       package manager hook callback

Options:
  -h, --help              show this help
  -V, --version           show version
  
Use "secbootctl [command] --help" for more information about a command.
```

To install bootloader, default kernel and update bootloader menu call the
following commands (command output is omitted):

```
~$ sudo secbootctl bootloader:install
~$ sudo secbootctl kernel:install
~$ sudo secbootctl bootloader:update-menu
```

If everything went well you can call `bootloader:status` just to verify 
everything is set up properly.

### Configuration

Listed below are all config options that can be customized by editing the
configuration file `/etc/secbootctl/secbootctl.conf`:

**`boot_path`** (default value: `/boot`)

Path of the boot directory that contains the unsigned original kernel, initramfs
and microcode images.

**`esp_path`** (default value: `/efi`)

Mount point of the EFI System Partition (ESP). In general the mount point is
"/boot", "/boot/efi" or "/efi".

see
also: [FAQ: Which mount point is recommended for the EFI System Partition (ESP)?](https://github.com/keaparrot/secbootctl#which-mount-point-is-recommended-for-the-efi-system-partition-esp)

**`sb_keys_path`** (default value: `/etc/secbootctl/keys`)

Path of the directory that contains the Secure Boot keys. For signing only the
Database Key (`db.key` and `db.crt`) is required.

see also [FAQ: How do I securely store my Secure Boot keys?](https://github.com/keaparrot/secbootctl#how-do-i-securely-store-my-secure-boot-keys)

**`kernel_image_name_prefix`** (default value: `vmlinuz`)

Prefix of the kernel image file names in the `<boot_path>` directory,
e.g. `vmlinuz-linux` where `vmlinuz` is the prefix. To be honest I'm not aware
of any distribution using a different prefix.

**`initramfs_image_name_template`** (default
value:  `initramfs-__kernel-name__.img`)

Name of the initramfs image files in the `<boot_path>` directory. Be sure to
replace the kernel name with the placeholder `__kernel-name__`. It will be
replaced internally by secbootctl when creating an unified kernel image. The
placeholder is required because of the different namings (e.g. Arch Linux names
it like `initramfs-linux.img` and Ubuntu like `initrd.img-5.10.0.15`).

**`microcode_image_name`** (default value:  `intel-ucode.img`)

Name of the microcode image file in the `<boot_path>` directory. Only relevant
if config option `include_microcode` is set to `yes`.

**`default_kernel`** (default value: `linux`)

Name of kernel that will be used for:

- `kernel:install` and `kernel:remove` if argument `kernel_name` is not given
- `bootloader:update-menu` to update the default bootloader menu entry

Expected as kernel name is the suffix of the kernel image under the
`<boot_path>` directory. For instance if the kernel image name
is `vmlinuz-5.4.0-91-generic` then the kernel name is `5.4.0-91-generic`.

Examples of valid kernel names:

- Arch Linux
    - `linux`, `linux-lts` etc.
- Ubuntu
    - `5.4.0-91-generic`

Apart from setting a fixed kernel name as described above it's also possible to
set the special config value `latest`. In that case the latest kernel will be
determined by sorting all kernel images by their name in descended order found
in the boot directory and choosing the first one. This is convenient for
distributions like Ubuntu because unlike Arch Linux when a new kernel gets
installed the existing kernel image will not be overridden but rather a new
kernel image will be added leaving the existing kernel images untouched. Hence
without using `latest` you have to manually update this config option everytime
a new kernel gets installed in case you always want the latest kernel set as
default bootloader menu entry.

**`include_microcode`** (default value: `yes`)

Whether the microcode image shall be included (`yes`) in the unified kernel
images or not (`no`).

For details
see: [Arch-Wiki: microcode](https://wiki.archlinux.org/title/microcode)

**`bootloader_menu_editor`** (default value: `no`)

Choose `yes` if kernel parameters should be editable otherwise `no`. Securitywise
it's advised to disable this option.

For details
see: [systemd-boot - loader.conf](https://www.freedesktop.org/software/systemd/man/loader.conf.html)

**`bootloader_menu_timeout`** (default value: `5`)

Time in seconds the booloader menu is shown before the default bootloader menu
entry is booted.

For details
see:[systemd-boot - loader.conf](https://www.freedesktop.org/software/systemd/man/loader.conf.html)

**`package_manager`** (default value: `pacman`)

Name of the package manager that will used when using package manager
integration feature.

### Package manager integration

For better usability it's very convenient to make use of the package manager of
your linux distribution that normally offer a way to hook into the packages
install, update and remove process. Instead of manually calling the appropriate
secbootctl commands after each kernel, initramfs, microcode or bootloader update
this can be done automatically by the package manager.

For supported package managers secbootctl offers hook files as well as a special
hook command (`pmi:hook-callback`) called by the hook. You can use `pmi:install`
command to install the hook files and as a result enable package manager
integration for the configured package manager. To disable package manager
integration use `pmi:remove` to remove the hook files.

Curently supported package managers:

- pacman (Arch Linux)
    - hook files:
        - `99-secbootctl-update.hook`
        - `99-secbootctl-remove.hook`
    - hook directory: `/etc/pacman.d`

## Limitations

Here you find a list of known limitations and issues:

- only relevant for Arch Linux:
    - Setting config value `latest` for `default_kernel` configuration doesn't
      make sense and therefore might not work as expected.
    - For an initramfs fallback image no additional unified kernel image will be
      created.
    - Currently pacman update hook (`pmi:hook-callback` command) always (re-)
      creates unified kernel images for all kernels found.
- only relevant for non Arch Linux distributions:
  - Change `package:manager` config option to something different than `pacman`
    otherwise `bootloader:update-menu` fails. As long as you don't 
    use the `pmi:` commands it doesn't matter if you set an unsupported 
    package manager.

## FAQ

### Which mount point is recommended for the EFI System Partition (ESP)?

Nowadays `/efi` seems to be the preferred ESP mount point as recommended
by [systemd](https://www.freedesktop.org/software/systemd/man/bootctl.html).
Nevertheless you can choose any other mount point like the often
used `/boot/efi`. When using a mount point other than `/efi` you have to set the
config option `esp_path` in the configuration file accordingly.

Securitywise you should not use `/boot` as ESP mount point. `/boot` contains the
unsigned original kernel, initramfs and microcode images that secbootctl uses to
create signed unified kernel images which will then be copied into the
appropriate directory on the ESP. Because the ESP is unencrypted an attacker
could do an evil maid attack by tampering any of the original images that you
might, unknowingly about the malicous changes, sign and boot afterwards. That's
why it's best practice to keep `/boot` encrypted and seperate from the
unencrypted ESP.

### What is an unified kernel image and why to use it?

An unified kernel image is just an EFI executable that contains everything that
is necessary for the UEFI firmware to boot Linux directly without the need of a
separate bootloader. In general such an image includes the following parts:

- kernel image
- initramfs image
- optionally microcode image (actually combined with the initramfs image
  beforehand)
- cmdline section
- os-release section
- EFI stub loader (e.g. systemd-boot EFI stub)

For details
see: [The Boot Loader Specification](https://systemd.io/BOOT_LOADER_SPECIFICATION/)

In order to really gain more security when using Secure Boot it is important
that each file loaded during the boot process gets verified and thus becomes
part of the so called boot chain of trust. For this very reason it is not enough
to only sign the kernel but to sign initramfs and microcode image as well.
Unfortunately there is one pitfall that might not be so obvious: to my knowledge
bootloaders like grub usually only verifying the kernel image by default. In
that case initramfs and microcode image could still be tampered. At this point
unified kernel images come in handy because when verified by the bootloader,
initramfs and microcode image are implicitly verified too.

### How do I securely store my Secure Boot keys?

Commonly Secure Boot keys are created with the `nodes` option of OpenSSL which 
means that the keys are stored unencrypted. I guess the reason is that it's
usually intended to use the keys in automated processes and manual passphrase 
input would be inconvenient. Because of that it's important that only root user 
has permissions to read the keys in `<sb_keys_path>`. If you followed the above
installation guide this directory should have permissions of `root:root:700` 
and the key files `root:root:400`. Moreover it is important that the partition 
on which the keys are stored is encrypted. At best you should use full disk
encryption (FDE) anyway.

Of course it would be more ideal if the Secure Boot keys are stored encrypted.
So if you don't mind to always enter your passphrase when using secbootctl for
signing, you can use encrypted keys as well. Far more secure it would be to use 
keys stored on a security token like a YubiKey. Moreover it might be possible
to encrypt the keys with the 
[TPM](https://en.wikipedia.org/wiki/Trusted_Platform_Module) like it is possible
with SSH keys and use them without the need of always entering the passphrase.
Currently neither the security token nor the TPM option is supported 
by secbootctl.

### Can I use my bootloader of choice?

Yes, but you won't get such a nice out of the box experience like you would get
when using secbootctl with the supported bootloader systemd-boot. That means
that you can still use secbootctl to e.g. create signed unified kernel images.
But you have to configure your bootloader on your own so that it loads these
images and lists them in its bootloader menu. Moreover you have to sign your
bootloader files manually too (you can use `file:sign` command for that).

<!--
## Contributions

Contributions are welcome and appreciated. Thus feel free to report issues,
bugs, feature requests, suggestions or alike.

It's my first open source project on github and I'm still learning how
everything works. So please don't mind if I may make some "mistakes" when
handling contributions.

I'm still working on a contribution guide as well as appropriate issue templates
and hope to release them soon.
-->

## Related projects

Of course there are also other noteworthy solutions that also inspired me when
developing secbootctl:

- [sicherboot](https://github.com/julian-klode/sicherboot)
- [sbupdate](https://github.com/andreyv/sbupdate)
- [sbctl](https://github.com/Foxboron/sbctl/)
- [safeboot](https://github.com/osresearch/safeboot)

## Related resources

Below a few resources with further more detailed information:

- Secure Boot
    - [Arch-Wiki: UEFI Secure Boot](https://wiki.archlinux.org/title/Secure_Boot)
    - [Gentoo-Wiki: UEFI Secure Boot](https://wiki.gentoo.org/wiki/User:Sakaki/Sakaki%27s_EFI_Install_Guide/Configuring_Secure_Boot)
    - [Rod Smith: Controlling Secure Boot](https://www.rodsbooks.com/efi-bootloaders/controlling-sb.html)
- systemd-boot & bootloader specification
    - [Arch-Wiki: systemd-boot](https://wiki.archlinux.org/title/systemd-boot)
    - [systemd: The Bootloader Specification](https://systemd.io/BOOT_LOADER_SPECIFICATION/)
    - [loader.conf - configuration file of systemd-boot](https://www.freedesktop.org/software/systemd/man/loader.conf.html)

## License

This project is released under the terms of the 
[MIT License](https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md).

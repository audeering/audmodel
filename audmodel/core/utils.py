import os
import zipfile
import errno
import tempfile

import audeer
import audfactory


def download_folder(root: str,
                    group_id: str,
                    repository: str,
                    name: str,
                    version: str,
                    *,
                    force: bool = False,
                    verbose: bool = False) -> str:

    server_url = audfactory.server_url(group_id,
                                       name=name,
                                       repository=repository,
                                       version=version)
    url = f'{server_url}/{name}-{version}.zip'
    src_path = os.path.join(tempfile._get_default_tempdir(), f'{name}.zip')
    dst_root = os.path.join(root, audeer.basename_wo_ext(src_path))
    dst_root = audeer.safe_path(dst_root)

    if force or not os.path.exists(dst_root):
        audeer.mkdir(dst_root)
        audfactory.download_artifact(url, src_path, verbose=verbose)
        unzip(src_path, dst_root, verbose=verbose)
        os.remove(src_path)

    return dst_root


def scan_files(root: str,
               sub_dir: str = '') -> (str, str):

    for entry in os.scandir(root):
        if entry.is_dir(follow_symlinks=False):
            yield from scan_files(entry.path,
                                  os.path.join(sub_dir, entry.name))
        else:
            yield sub_dir, entry.name


def unzip(src_path: str, dst_root: str, *, verbose: bool = False) -> None:

    with zipfile.ZipFile(src_path, 'r') as zf:
        if verbose:
            members = zf.infolist()
            with audeer.progress_bar(members,
                                     total=len(members),
                                     desc='') as pbar:
                for member in pbar:
                    desc = audeer.format_display_message(f'Unzip '
                                                         f'{member.filename}',
                                                         pbar=True)
                    pbar.set_description_str(desc, refresh=True)
                    zf.extract(member, dst_root)
        else:
            zf.extractall(dst_root)


def upload_folder(root: str,
                  group_id: str,
                  repository: str,
                  name: str,
                  version: str,
                  *,
                  force: bool = False,
                  verbose: bool = False) -> str:

    root = audeer.safe_path(root)
    if not os.path.isdir(root):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                root)

    server_url = audfactory.server_url(group_id,
                                       name=name,
                                       repository=repository,
                                       version=version)
    url = f'{server_url}/{name}-{version}.zip'

    if force or not audfactory.artifactory_path(url).exists():
        src_path = os.path.join(tempfile._get_default_tempdir(),
                                f'{name}-{version}.zip')
        zip_folder(root, src_path, verbose=verbose)
        audfactory.upload_artifact(src_path,
                                   repository,
                                   group_id,
                                   name,
                                   version,
                                   verbose=verbose)
        os.remove(src_path)

    return url


def zip_folder(src_root: str, dst_path: str, *, verbose: bool = False) -> None:

    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        files = list(scan_files(src_root))
        if verbose:
            with audeer.progress_bar(files,
                                     total=len(files),
                                     desc='') as pbar:
                for base, file in pbar:
                    path = os.path.join(src_root, base, file)
                    desc = audeer.format_display_message(f'Zip {path}',
                                                         pbar=True)
                    pbar.set_description_str(desc, refresh=True)
                    zf.write(path, arcname=os.path.join(base, file))
        else:
            for base, file in files:
                zf.write(os.path.join(src_root, base, file),
                         arcname=os.path.join(base, file))

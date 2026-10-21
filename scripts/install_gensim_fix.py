"""Build a reproducible local Gensim 4.4.0 patch for legitimate BLAS dot=-1.

Upstream license and source notices are preserved. No binaries are committed.
Run using the target Python environment, after requirements-study.lock.
"""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://files.pythonhosted.org/packages/1a/80/fe9d2e1ace968041814dbcfce4e8499a643a36c41267fa4b6c4f54cce420/gensim-4.4.0.tar.gz'
SHA256 = 'a3f5b626da5518e79a479140361c663089fe7998df8ba52d56e1ded71ac5bdf5'
VERSION = '4.4.0+wnm1'
FASTSS_URL = 'https://raw.githubusercontent.com/piskvorky/gensim/4.4.0/gensim/similarities/fastss.pyx'
FASTSS_SHA256 = '28ef4b96570b64b674959f7900cc8786ab22df0c5871b6b9c9ee75a8a0241d1e'
PROBE = '''

# Wikipedia Navigation Mining local patch: regression probe, no training changes.
def _wikinav_negative_dot_check():
    cdef int size = 1
    cdef int stride = 1
    cdef REAL_t x = -1.0
    cdef REAL_t y = 1.0
    return float(our_dot(&size, &x, &stride, &y, &stride))
'''


def run():
    try:
        if importlib.metadata.version('gensim') == VERSION:
            from gensim.models.word2vec_inner import _wikinav_negative_dot_check
            if _wikinav_negative_dot_check() != -1.0:
                raise RuntimeError('Patched BLAS probe failed')
            print('Verified Gensim', VERSION, 'negative-dot probe')
            return
    except importlib.metadata.PackageNotFoundError:
        pass
    cache = ROOT / '.cache/gensim-build'
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / 'gensim-4.4.0.tar.gz'
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error', '--retry', '3',
                        '--continue-at', '-', '--max-time', '600', URL, '-o', str(archive)], check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError('Unverified Gensim archive; refusing build')
    fastss = cache / 'fastss.pyx'
    if not fastss.exists():
        subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','60',FASTSS_URL,'-o',str(fastss)],check=True)
    if hashlib.sha256(fastss.read_bytes()).hexdigest() != FASTSS_SHA256:
        raise RuntimeError('Unverified supplementary fastss source')
    with tempfile.TemporaryDirectory(prefix='patched-', dir=cache) as tmp:
        with tarfile.open(archive) as tar:
            tar.extractall(tmp, filter='data')
        source = Path(tmp) / 'gensim-4.4.0'
        (source / 'gensim/similarities/fastss.pyx').write_bytes(fastss.read_bytes())
        pxd = source / 'gensim/models/word2vec_inner.pxd'
        original = pxd.read_text()
        if original.count('except -1 nogil') != 2:
            raise RuntimeError('Unexpected upstream BLAS declarations')
        pxd.write_text(original.replace('except -1 nogil', 'noexcept nogil'))
        pyx = source / 'gensim/models/word2vec_inner.pyx'
        pyx.write_text(pyx.read_text() + PROBE)
        setup = source / 'setup.py'
        assert setup.read_text().count("version='4.4.0'") == 1
        setup.write_text(setup.read_text().replace("version='4.4.0'", f"version='{VERSION}'"))
        init = source / 'gensim/__init__.py'
        init.write_text(init.read_text().replace("'4.4.0'", repr(VERSION)))
        # Regenerate all extensions: bundled C predates Python 3.13. The missing
        # fastss.pyx is restored from the checksum-pinned upstream release tag.
        subprocess.run([sys.executable, '-c',
            "from pathlib import Path; from setuptools import Extension; "
            "from Cython.Build import cythonize; "
            "cpp={'doc2vec_inner','word2vec_corpusfile','fasttext_corpusfile','doc2vec_corpusfile'}; "
            "cythonize([Extension('.'.join(p.with_suffix('').parts),[str(p)],language='c++' if p.stem in cpp else 'c') "
            "for p in Path('gensim').rglob('*.pyx')],force=True,compiler_directives={'language_level':3})"],
            cwd=source, check=True)
        wheels = Path(tmp) / 'wheels'
        subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
                        '--wheel-dir', str(wheels), str(source)], check=True)
        wheel, = wheels.glob('gensim-*.whl')
        provenance = {'upstream_url': URL, 'upstream_sha256': SHA256, 'version': VERSION,
                      'fastss_url':FASTSS_URL,'fastss_sha256':FASTSS_SHA256,
                      'installer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
                      'build_versions': {name: importlib.metadata.version(name)
                                         for name in ('Cython', 'setuptools', 'wheel', 'numpy')}}
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--force-reinstall', str(wheel)], check=True)
        (cache / 'build_manifest.json').write_text(json.dumps(provenance, indent=2)+'\n')
    subprocess.run([sys.executable, '-c',
        'from gensim.models.word2vec_inner import _wikinav_negative_dot_check; '
        'assert _wikinav_negative_dot_check() == -1.0; print("BLAS dot=-1 regression passed")'], check=True)


if __name__ == '__main__':
    run()

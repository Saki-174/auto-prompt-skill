"""Installer-only permission snapshots and private staging (no extra dependency).

Windows preserves owner, primary group and DACL; SACL/audit policy is outside
this unprivileged installer. Unsupported restoration fails before publishing.
"""
import ctypes
import os
import re
import stat
import uuid
from pathlib import Path

if os.name == "nt":
    from ctypes import wintypes as w
    import msvcrt

    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    P = ctypes.c_void_p
    class SecurityAttributes(ctypes.Structure):
        _fields_ = [("length", w.DWORD), ("descriptor", P), ("inherit", w.BOOL)]

    def api(dll, name, args, result):
        function = getattr(dll, name)
        function.argtypes, function.restype = args, result
        return function

    get_security = api(adv, "GetFileSecurityW", [w.LPCWSTR, w.DWORD, P, w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL)
    to_string = api(adv, "ConvertSecurityDescriptorToStringSecurityDescriptorW", [P, w.DWORD, w.DWORD, ctypes.POINTER(P), P], w.BOOL)
    from_string = api(adv, "ConvertStringSecurityDescriptorToSecurityDescriptorW", [w.LPCWSTR, w.DWORD, ctypes.POINTER(P), P], w.BOOL)
    get_dacl = api(adv, "GetSecurityDescriptorDacl", [P, ctypes.POINTER(w.BOOL), ctypes.POINTER(P), ctypes.POINTER(w.BOOL)], w.BOOL)
    get_control = api(adv, "GetSecurityDescriptorControl", [P, ctypes.POINTER(w.WORD), ctypes.POINTER(w.DWORD)], w.BOOL)
    set_file_security = api(adv, "SetFileSecurityW", [w.LPCWSTR, w.DWORD, P], w.BOOL)
    create_file = api(kernel, "CreateFileW", [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.POINTER(SecurityAttributes), w.DWORD, w.DWORD, w.HANDLE], w.HANDLE)
    create_dir = api(kernel, "CreateDirectoryW", [w.LPCWSTR, ctypes.POINTER(SecurityAttributes)], w.BOOL)
    close = api(kernel, "CloseHandle", [w.HANDLE], w.BOOL)
    free = api(kernel, "LocalFree", [P], P)
    open_token = api(adv, "OpenProcessToken", [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)], w.BOOL)
    token_info = api(adv, "GetTokenInformation", [w.HANDLE, ctypes.c_int, P, w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL)
    sid_string = api(adv, "ConvertSidToStringSidW", [P, ctypes.POINTER(P)], w.BOOL)
    process = api(kernel, "GetCurrentProcess", [], w.HANDLE)

    def checked(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return result

    def descriptor(sddl):
        pointer = P()
        checked(from_string(sddl, 1, ctypes.byref(pointer), None))
        return pointer

    def private_sddl():
        token = w.HANDLE()
        checked(open_token(process(), 8, ctypes.byref(token)))
        try:
            size = w.DWORD()
            token_info(token, 1, None, 0, ctypes.byref(size))
            buffer = ctypes.create_string_buffer(size.value)
            checked(token_info(token, 1, buffer, size, ctypes.byref(size)))
            text = P()
            checked(sid_string(ctypes.cast(buffer, ctypes.POINTER(P))[0], ctypes.byref(text)))
            try:
                sid = ctypes.wstring_at(text)
            finally:
                free(text)
        finally:
            close(token)
        return "D:P(A;OICI;FA;;;" + sid + ")(A;OICI;FA;;;SY)"


def capture(path):
    """Do not read SACL or request/enable elevated privileges."""
    if os.name != "nt":
        return {"mode": stat.S_IMODE(Path(path).stat().st_mode)}
    size = w.DWORD()
    get_security(str(path), 7, None, 0, ctypes.byref(size))
    if not size.value:
        raise ctypes.WinError(ctypes.get_last_error())
    buffer = ctypes.create_string_buffer(size.value)
    checked(get_security(str(path), 7, buffer, size, ctypes.byref(size)))
    text = P()
    checked(to_string(buffer, 1, 7, ctypes.byref(text), None))
    try:
        # AI/AR record Windows auto-inheritance bookkeeping, not access rights.
        # Preserve protection (P), ACE inheritance flags, owner and group.
        sddl = re.sub(r"D:[^()]*", lambda match: match[0].replace("AI", "").replace("AR", ""), ctypes.wstring_at(text))
        return {"sddl": sddl}
    finally:
        free(text)


def apply(path, snapshot):
    if os.name != "nt":
        os.chmod(path, snapshot["mode"])
        return
    sd = descriptor(snapshot["sddl"])
    try:
        dacl = P()
        defaulted, present = w.BOOL(), w.BOOL()
        checked(get_dacl(sd, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)))
        if not present:
            raise ValueError("missing DACL; cannot preserve permissions safely")
        control, revision = w.WORD(), w.DWORD()
        checked(get_control(sd, ctypes.byref(control), ctypes.byref(revision)))
        # This compatibility API restores the descriptor without propagating
        # new inherited ACEs from the private staging parent. SetSecurityInfo
        # would merge that parent's DACL and change the captured permissions.
        flags = 7 | (0x80000000 if control.value & 0x1000 else 0x20000000)
        checked(set_file_security(str(path), flags, sd))
    finally:
        free(sd)
    if capture(path) != snapshot:
        raise ValueError("permissions could not be preserved exactly; installation stopped")


def mkdir_private(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.mkdir(mode=0o700)
        return
    expected = private_sddl()
    sd = descriptor(expected)
    try:
        attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), sd, False)
        checked(create_dir(str(path), ctypes.byref(attributes)))
    finally:
        free(sd)
    if capture(path)["sddl"].partition("D:")[2] != expected.partition("D:")[2]:
        raise ValueError("filesystem did not enforce private transaction ACL; installation stopped")


def private_file(path):
    """Create empty file privately, before any sensitive bytes are written."""
    if os.name != "nt":
        return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    expected = private_sddl()
    sd = descriptor(expected)
    try:
        attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), sd, False)
        handle = create_file(str(path), 0x40000000, 7, ctypes.byref(attributes), 1, 0x80, None)
        if handle == P(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if capture(path)["sddl"].partition("D:")[2] != expected.partition("D:")[2]:
                raise ValueError("filesystem did not enforce private temporary ACL; installation stopped")
            return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
        except Exception:
            close(handle)
            raise
    finally:
        free(sd)


def temporary_file(parent):
    path = Path(parent) / (".auto-prompt-" + uuid.uuid4().hex)
    return private_file(path), path

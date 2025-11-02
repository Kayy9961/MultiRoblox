import ctypes as ct
from ctypes import wintypes
import psutil, time, sys

PROCESS_NAME = "RobloxPlayerBeta.exe"
TARGET_EVENT_BASENAME = "ROBLOX_singletonEvent"
TARGET_VARIANTS = [
    rf"\Sessions\1\BaseNamedObjects\{TARGET_EVENT_BASENAME}",
    rf"\BaseNamedObjects\{TARGET_EVENT_BASENAME}",
    rf"Local\{TARGET_EVENT_BASENAME}",
]

kernel32 = ct.WinDLL("kernel32", use_last_error=True)
advapi32 = ct.WinDLL("advapi32", use_last_error=True)
ntdll    = ct.WinDLL("ntdll",    use_last_error=True)

SE_DEBUG_NAME = "SeDebugPrivilege"
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

PROCESS_DUP_HANDLE = 0x0040
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

DUPLICATE_CLOSE_SOURCE = 0x00000001
DUPLICATE_SAME_ACCESS  = 0x00000002

SystemHandleInformation = 16
SystemExtendedHandleInformation = 64
STATUS_SUCCESS = 0
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004

ObjectNameInformation = 1
ObjectTypeInformation = 2

HANDLE = wintypes.HANDLE
ULONG  = wintypes.ULONG
DWORD  = wintypes.DWORD
BOOL   = wintypes.BOOL
LPCWSTR = wintypes.LPCWSTR

class SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX(ct.Structure):
    _fields_ = [
        ("Object", ct.c_void_p),
        ("UniqueProcessId", ct.c_ulonglong),
        ("HandleValue", ct.c_void_p),
        ("GrantedAccess", wintypes.ULONG),
        ("CreatorBackTraceIndex", wintypes.USHORT),
        ("ObjectTypeIndex", wintypes.USHORT),
        ("HandleAttributes", wintypes.ULONG),
        ("Reserved", wintypes.ULONG),
    ]

class SYSTEM_HANDLE_INFORMATION_EX(ct.Structure):
    _fields_ = [("NumberOfHandles", ct.c_ulonglong), ("Reserved", ct.c_ulonglong)]

class SYSTEM_HANDLE_TABLE_ENTRY_INFO(ct.Structure):
    _fields_ = [
        ("UniqueProcessId", wintypes.USHORT),
        ("CreatorBackTraceIndex", wintypes.USHORT),
        ("ObjectTypeIndex", wintypes.BYTE),
        ("HandleAttributes", wintypes.BYTE),
        ("HandleValue", wintypes.USHORT),
        ("Object", ct.c_void_p),
        ("GrantedAccess", wintypes.ULONG),
    ]

class SYSTEM_HANDLE_INFORMATION_LEGACY(ct.Structure):
    _fields_ = [("NumberOfHandles", wintypes.ULONG)]

class UNICODE_STRING(ct.Structure):
    _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT), ("Buffer", wintypes.LPWSTR)]

class _USTR(ct.Structure):
    _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT), ("Buffer", wintypes.LPWSTR)]

kernel32.GetCurrentProcess.restype  = HANDLE
kernel32.GetCurrentProcess.argtypes = []
kernel32.OpenProcess.restype        = HANDLE
kernel32.OpenProcess.argtypes       = [DWORD, BOOL, DWORD]
kernel32.CloseHandle.restype        = BOOL
kernel32.CloseHandle.argtypes       = [HANDLE]
kernel32.DuplicateHandle.restype    = BOOL
kernel32.DuplicateHandle.argtypes   = [HANDLE, HANDLE, HANDLE, ct.POINTER(HANDLE), DWORD, BOOL, DWORD]

advapi32.OpenProcessToken.restype   = BOOL
advapi32.OpenProcessToken.argtypes  = [HANDLE, DWORD, ct.POINTER(HANDLE)]
advapi32.LookupPrivilegeValueW.restype = BOOL
advapi32.LookupPrivilegeValueW.argtypes = [LPCWSTR, LPCWSTR, ct.c_void_p]
advapi32.AdjustTokenPrivileges.restype = BOOL
advapi32.AdjustTokenPrivileges.argtypes= [HANDLE, BOOL, ct.c_void_p, DWORD, ct.c_void_p, ct.c_void_p]

NTSTATUS = wintypes.LONG
ntdll.NtQuerySystemInformation.restype  = NTSTATUS
ntdll.NtQuerySystemInformation.argtypes = [ULONG, ct.c_void_p, ULONG, ct.POINTER(ULONG)]
ntdll.NtQueryObject.restype  = NTSTATUS
ntdll.NtQueryObject.argtypes = [HANDLE, ULONG, ct.c_void_p, ULONG, ct.POINTER(ULONG)]

def norm(st: int) -> int:
    return st & 0xFFFFFFFF

def enable_debug_privilege():
    class LUID(ct.Structure):
        _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]
    class LUID_AND_ATTRIBUTES(ct.Structure):
        _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]
    class TOKEN_PRIVILEGES(ct.Structure):
        _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]

    token = HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ct.byref(token)):
        raise OSError(ct.get_last_error(), "OpenProcessToken")
    luid = LUID()
    if not advapi32.LookupPrivilegeValueW(None, SE_DEBUG_NAME, ct.byref(luid)):
        kernel32.CloseHandle(token); raise OSError(ct.get_last_error(), "LookupPrivilegeValueW")
    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
    if not advapi32.AdjustTokenPrivileges(token, False, ct.byref(tp), 0, None, None):
        kernel32.CloseHandle(token); raise OSError(ct.get_last_error(), "AdjustTokenPrivileges")
    kernel32.CloseHandle(token)

def get_pid_by_name(name: str):
    for p in psutil.process_iter(["pid","name"]):
        if p.info["name"] and p.info["name"].lower() == name.lower():
            return p.info["pid"]
    return None

def query_handles_extended():
    size = 0x10000
    while True:
        buf = ct.create_string_buffer(size); ret = ULONG(0)
        s = ntdll.NtQuerySystemInformation(SystemExtendedHandleInformation, buf, size, ct.byref(ret))
        s = norm(int(s))
        if s == STATUS_SUCCESS:
            break
        if s != STATUS_INFO_LENGTH_MISMATCH:
            raise OSError(s, "NtQuerySystemInformation(64)")
        size = max(size*2, ret.value or size*2)
        if size > 64*1024*1024:
            raise MemoryError("Handle list too large (64)")

    base = ct.addressof(buf)
    header = SYSTEM_HANDLE_INFORMATION_EX.from_buffer(buf)
    count = header.NumberOfHandles
    entry_sz = ct.sizeof(SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX)
    start = base + ct.sizeof(SYSTEM_HANDLE_INFORMATION_EX)

    entries = []
    for i in range(count):
        e = SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX.from_address(start + i*entry_sz)
        entries.append((int(e.UniqueProcessId), int(ct.c_size_t(e.HandleValue).value)))
    return entries

def query_handles_legacy():
    size = 0x10000
    while True:
        buf = ct.create_string_buffer(size); ret = ULONG(0)
        s = ntdll.NtQuerySystemInformation(SystemHandleInformation, buf, size, ct.byref(ret))
        s = norm(int(s))
        if s == STATUS_SUCCESS:
            break
        if s != STATUS_INFO_LENGTH_MISMATCH:
            raise OSError(s, "NtQuerySystemInformation(16)")
        size = max(size*2, ret.value or size*2)
        if size > 64*1024*1024:
            raise MemoryError("Handle list too large (16)")

    base = ct.addressof(buf)
    header = SYSTEM_HANDLE_INFORMATION_LEGACY.from_buffer(buf)
    count = header.NumberOfHandles
    entry_sz = ct.sizeof(SYSTEM_HANDLE_TABLE_ENTRY_INFO)
    start = base + ct.sizeof(SYSTEM_HANDLE_INFORMATION_LEGACY)

    entries = []
    for i in range(count):
        e = SYSTEM_HANDLE_TABLE_ENTRY_INFO.from_address(start + i*entry_sz)
        entries.append((int(e.UniqueProcessId), int(e.HandleValue)))
    return entries

def query_handles_unified():
    try:
        return query_handles_extended()
    except Exception:
        return query_handles_legacy()

def dup_to_self(hProc: HANDLE, hRemote: int):
    hDup = HANDLE()
    ok = kernel32.DuplicateHandle(
        hProc, HANDLE(hRemote), kernel32.GetCurrentProcess(),
        ct.byref(hDup), 0, False, DUPLICATE_SAME_ACCESS
    )
    return hDup if ok else None

def nt_str(h, info_class):
    need = ULONG(0)
    _ = ntdll.NtQueryObject(h, info_class, None, 0, ct.byref(need))
    if not need.value:
        return None
    buf = ct.create_string_buffer(need.value)
    s = ntdll.NtQueryObject(h, info_class, buf, need.value, None)
    if norm(int(s)) != STATUS_SUCCESS:
        return None
    u = _USTR.from_buffer(buf)
    if not u.Buffer or not u.Length:
        return None
    try:
        return u.Buffer[:u.Length//2]
    except Exception:
        return (u.Buffer[:u.Length//2]).encode("utf-8","replace").decode("utf-8")

def close_remote(hProc: HANDLE, hRemote: int) -> bool:
    dummy = HANDLE()
    ok = kernel32.DuplicateHandle(
        hProc, HANDLE(hRemote), None, ct.byref(dummy), 0, False,
        DUPLICATE_CLOSE_SOURCE | DUPLICATE_SAME_ACCESS
    )
    return bool(ok)

def main():
    print("🔧 Iniciando Roblox Event Closer\n")
    try:
        enable_debug_privilege()
    except Exception as e:
        print(f"❌ Error al habilitar SeDebugPrivilege: {e}")
        print("   Ejecuta como Administrador.")
        input("\nPulsa Enter para salir...")
        return

    pid = get_pid_by_name(PROCESS_NAME)
    if not pid:
        print("🚫 Roblox no está en ejecución.")
        print("➡️  Ábrelo y vuelve a ejecutar este programa.")
        print("⏳ Cerrando en 5 segundos...")
        time.sleep(5)
        return

    print(f"✅ Roblox detectado (PID {pid}) — Escaneando…")
    hProc = kernel32.OpenProcess(PROCESS_DUP_HANDLE | PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not hProc:
        print("⚠️  OpenProcess falló (¿Administrador?)")
        input("\nPulsa Enter para salir...")
        return

    closed = 0
    total = 0
    try:
        entries = query_handles_unified()
        for upid, hval in entries:
            if upid != pid:
                continue
            total += 1

            hLocal = dup_to_self(hProc, hval)
            if not hLocal:
                continue
            try:
                typ = nt_str(hLocal, ObjectTypeInformation)
                if not typ or typ.lower() != "event":
                    continue
                name = nt_str(hLocal, ObjectNameInformation) or ""
                if any(name.lower().endswith(v.lower()) for v in TARGET_VARIANTS):
                    if close_remote(hProc, hval):
                        closed += 1
                        print(f"✨ Cerrada handle de '{name}'")
            finally:
                kernel32.CloseHandle(hLocal)
    finally:
        kernel32.CloseHandle(hProc)

    print(f"\n📊 Handles analizadas: {total}")
    if closed:
        print(f"🎉 Cerradas {closed} handle(s) del evento {TARGET_EVENT_BASENAME}.")
    else:
        print(f"🔍 No se encontró ninguna handle del evento {TARGET_EVENT_BASENAME}.")
    print("\n💡 Fin. Pulsa Enter para salir.")
    input()

if __name__ == "__main__":
    main()

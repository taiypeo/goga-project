_perm_names: list = [
    "post",
    "create_subgroups",
    "invite_admins",
    "invite_posters",
    "invite_students"
]

class PermissionsBase:
    def _get_mapped(self):
        raise NotImplementedError()

    def _set_mapped(self):
        raise NotImplementedError()

    def enable(self, *args):
        '''
        Enable all permissions from args

        >>> permissions.enable('post', 'create_subgroups')
        '''
        for perm in args:
            if perm in _perm_names:
                self._set_mapped(self._get_mapped() | (1 << _perm_names.index(perm)))
            else:
                raise ValueError(f'{perm} is not valid permission')

    def is_enabled(self, *args) -> bool:
        '''
        Check that all of permissions from args are enabled
        '''
        res = True
        for perm in args:
            if perm in _perm_names:
                res &= bool(self._get_mapped() & (1 << _perm_names.index(perm)))
            else:
                raise ValueError(f'{perm} is not valid permission')
        return res
    
    def disable(self, *args):
        '''
        Disable all permissions from args
        '''
        for perm in args:
            if perm in _perm_names:
                self._set_mapped(
                    self._get_mapped() & (~(1 << _perm_names.index(perm)))
                )

    def enable_from(self, perms: PermissionsBase):
        self.set_mapped(self._get_mapped() | perms._get_mapped())
    
    def clear(self):
        '''
        Disable all permissions
        '''
        self._set_mapped(0)
    
    def __int__(self):
        return self._get_mapped()

    def __repr__(self) -> str:
        return ' '.join(
            perm for off, perm in enumerate(_perm_names)
            if (self._get_mapped() & (1 << off))
        )


class BindedPermissions(PermissionsBase):
    def __init__(self, mapping, attr_name):
        self.mapping = mapping
        self.attr_name = attr_name

    def _get_mapped(self):
        return getattr(self.mapping, self.attr_name)
    
    def _set_mapped(self, val):
        setattr(self.mapping, self.attr_name, val)


class UnbindedPermissions(PermissionsBase):
    def __init__(self, *args):
        self.mask = 0
        self.enable(*args)
    
    def _get_mapped(self):
        return self.mask
    
    def _set_mapped(self, val):
        self.mask = val

from django.db import models


class Machine(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.CharField(db_column="ip", max_length=16)
    type = models.IntegerField(db_column="type")
    status = models.IntegerField(db_column="status")
    ext = models.TextField(db_column="ext")
    description = models.CharField(null=True, db_column="description", max_length=50)
    user = models.CharField(null=True, db_column="user", max_length=10)
    use_start_time = models.DateTimeField(null=True, db_column="use_start_time")
    use_message = models.CharField(null=True, db_column="use_message", max_length=50)
    tag = models.CharField(null=True, db_column="tag", max_length=20)

    class Meta:
        db_table = "machine"


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10)
    desc = models.CharField(max_length=50)

    class Meta:
        db_table = "tag"


class OS(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        db_table = "os_type"


class InvGroup(models.Model):
    """
    inventory ·Ö×é £¨×Ê²ú·Ö×é£©
    """
    id = models.AutoField(primary_key=True)
    inv_id = models.BigIntegerField()
    name = models.CharField(max_length=20, blank=True, null=True)
    note = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'odin_inv_group'


class HostModel(models.Model):
    """
    host
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=10, blank=True, null=True)
    ip = models.CharField(max_length=10, blank=True, null=True)
    ssh_user = models.CharField(max_length=10, blank=True, null=True)
    ssh_password = models.CharField(max_length=20, blank=True, null=True)
    ssh_port = models.CharField(max_length=10, default="22")
    gid = models.BigIntegerField()
    inv_id = models.BigIntegerField()
    create_time = models.DateTimeField(db_column="createtime")
    update_time = models.DateTimeField(db_column="updatetime")
    var = models.TextField(default="{}")

    class Meta:
        managed = False
        db_table = 'odin_host'

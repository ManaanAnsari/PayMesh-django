from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager
)
from django.contrib.auth.hashers import make_password 
from django.contrib.auth.models import PermissionsMixin



class UserManager(BaseUserManager):
    
    def create_user(self,web3_address, email,password):
        user = self.model(web3_address=web3_address,email=email,password=make_password(password))
        user.save()

        return user

    def create_superuser(self, web3_address,password):

        user = self.create_user(web3_address=web3_address,password=password,email=None)
        user.is_superuser = True
        user.save()

        return user


class User(AbstractBaseUser, PermissionsMixin):
    web3_address = models.CharField(max_length=100,unique=True)    
    email = models.EmailField(blank=True, null= True, default=None, unique=True)
    name = models.CharField(max_length=150,blank=True, null= True, default=None)
    
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    username=None
    objects = UserManager()
    
    USERNAME_FIELD = 'web3_address'
    REQUIRED_FIELDS = []

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_superuser
    
    def __str__(self) -> str:
        return self.web3_address + " " + self.name if self.name else self.web3_address


# Create your models here.
class UserCaptcha(models.Model):
    captcha = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = "user_captcha"



class Web3Address(models.Model):
    ADDRESS_TYPES = (
        ('EVM', 'EVM'),
    )

    ADDRESS_TYPES_LIST = [v[0] for v in ADDRESS_TYPES]
   
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPES,
        default="EVM",
    )
    
    address = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    human_name = models.CharField(max_length=100,blank=True, null= True, default=None)
    
    
    def __str__(self) -> str:
        return self.address[-4:] + "#"+ str(self.user.id) 
    
    class Meta:
        db_table = "web3address"
        

class UserGateWeb3Account(models.Model):
    ADDRESS_TYPES = (
        ('EVM', 'EVM'),
    )

    ADDRESS_TYPES_LIST = [v[0] for v in ADDRESS_TYPES]
   
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPES,
        default="EVM",
    )
    
    address = models.CharField(max_length=100)
    private_key = models.CharField(max_length=256)
    mnemonic = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self) -> str:
        return self.address[-4:] + "#"+ str(self.user.id) 
    
    class Meta:
        db_table = "gate_web3_account"
        



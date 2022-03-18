from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Professor(models.Model):
    name = models.CharField(max_length=100)
    professor_id = models.CharField(max_length=4, primary_key=True, default='OOO')

    def __str__(self):
        return self.name

class Module(models.Model):
    module_name = models.CharField(max_length=100)
    module_code = models.CharField(max_length=3,primary_key=True, default='OOO')

    def __str__(self):
        return ("Module Name: {0} ({1})".format(self.module_name, self.module_code))

class ModuleInstance(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    academic_year = models.IntegerField(default=2000)
    semester = models.IntegerField(default='1', validators=[MaxValueValidator(3), MinValueValidator(1)])
    professors = models.ManyToManyField(Professor, blank=False)

    def __str__(self):
        return ("Code: {0} Name: {1} Year: {2} Semester: {3}".format(self.module.module_code, self.module.module_name, 
                                             self.academic_year, self.semester))

class Rating(models.Model):
    rating = models.IntegerField(blank=False, validators=[MaxValueValidator(5), MinValueValidator(1)])
    professor_reference = models.ForeignKey(Professor, on_delete=models.CASCADE)
    module_reference = models.ForeignKey(ModuleInstance, on_delete=models.CASCADE)

    def __str__(self):
        return ("A rating of {0} for professor {1} in module {2}".format(self.rating, self.professor_reference.name, self.module_reference.module.module_code))

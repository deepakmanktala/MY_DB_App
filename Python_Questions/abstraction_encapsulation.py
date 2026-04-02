from abc import ABC, abstractmethod
class BankAccount(ABC):
    @abstractmethod
    def balance(self):
        pass

class AnimalAccount(BankAccount):
    def balance(self):
        pass
class Animal(ABC):
    @abstractmethod
    def eat(self):
        pass
    @abstractmethod
    def drink(self):
        pass
    @abstractmethod
    def make_sound(self):
        pass

class Dog(Animal):
    def eat(self):
        print("eat chicken")
    def make_sound(self):
        print("bark")
    def drink(self):
        print("drink water")

animal = Dog()
animal.make_sound()
animal.eat()




class Vehicle(ABC):
    @abstractmethod
    def drive(self):
        print(" You have to drive me")
    @abstractmethod
    def tyres(self):
        print("My tyres")

class Car(Vehicle):
    def drive(self):
        print("I am a self driven Car")

    def tyres(self):
        print("I am a self tyres")

car = Car()
car.drive()
car.tyres()
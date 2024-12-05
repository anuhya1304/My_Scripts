from rest_framework import serializers
from .models import Category, Product
from .utils import encrypt_price, decrypt_price


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.FloatField(write_only=True)
    decrypted_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description',
                  'price', 'decrypted_price', 'category']

    def create(self, validated_data):
        price = validated_data.pop('price')
        validated_data['price'] = encrypt_price(price)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'price' in validated_data:
            instance.price = encrypt_price(validated_data.pop('price'))
        return super().update(instance, validated_data)

    def get_decrypted_price(self, obj):
        return decrypt_price(obj.price)

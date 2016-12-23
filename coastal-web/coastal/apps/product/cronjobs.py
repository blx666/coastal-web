from coastal.apps.account.models import FavoriteItem
from coastal.apps.product.models import Product, ProductViewCount


def update_product_score():
    products = Product.objects.all()
    for product in products:
        score = 0
        product_view_count = ProductViewCount.objects.filter(product=product).first()
        if product_view_count:
            score += product_view_count.count
        liked_count = FavoriteItem.objects.filter(product=product).count()
        product.score = score + 7 * liked_count
        product.save()

"""
Tests for Collection and CollectionProduct models.
"""

from app.models.project import Project
from app.models.product import Product
from app.models.collection import Collection, CollectionProduct


class TestCollection:
    """Test Collection model functionality."""

    def test_collection_creation(self, session):
        """Test creating a collection."""
        collection = Collection(
            name="My Collection", description="A test collection", is_public=True
        )
        session.add(collection)
        session.commit()

        assert collection.id is not None
        assert collection.name == "My Collection"
        assert collection.description == "A test collection"
        assert collection.is_public is True
        assert collection.product_count == 0
        assert collection.cover_product_id is None

    def test_collection_defaults(self, session):
        """Test collection default values."""
        collection = Collection(name="Test Collection")
        session.add(collection)
        session.commit()

        assert collection.description is None
        assert collection.is_public is False
        assert collection.product_count == 0
        assert collection.cover_product_id is None

    def test_add_product_method(self, session):
        """Test adding a product to collection."""
        collection = Collection(name="Test Collection")
        session.add(collection)
        session.commit()

        # Add product with automatic position
        association = collection.add_product("product-1")
        assert association.collection_id == collection.id
        assert association.product_id == "product-1"
        assert association.position == 0
        assert collection.product_count == 1

        # Add product with specific position
        association2 = collection.add_product("product-2", position=5)
        assert association2.position == 5
        assert collection.product_count == 2

    def test_remove_product_method(self, session):
        """Test removing a product from collection."""
        collection = Collection(name="Test Collection", product_count=3)
        session.add(collection)
        session.commit()

        collection.remove_product("product-1")
        assert collection.product_count == 2

        # Can't go below zero
        collection.product_count = 1
        collection.remove_product("product-2")
        assert collection.product_count == 0

        collection.remove_product("product-3")
        assert collection.product_count == 0

    def test_reorder_products_method(self, session):
        """Test reordering products in collection."""
        collection = Collection(name="Test Collection")
        session.add(collection)
        session.commit()

        # Create collection products
        cp1 = CollectionProduct(
            collection_id=collection.id, product_id="prod-1", position=0
        )
        cp2 = CollectionProduct(
            collection_id=collection.id, product_id="prod-2", position=1
        )
        cp3 = CollectionProduct(
            collection_id=collection.id, product_id="prod-3", position=2
        )

        collection.products = [cp1, cp2, cp3]
        session.commit()

        # Reorder: prod-3, prod-1, prod-2
        collection.reorder_products(["prod-3", "prod-1", "prod-2"])

        assert cp3.position == 0
        assert cp1.position == 1
        assert cp2.position == 2

    def test_update_count_method(self, session):
        """Test updating product count."""
        collection = Collection(name="Test Collection")
        session.add(collection)
        session.commit()

        # Add some collection products
        cp1 = CollectionProduct(collection_id=collection.id, product_id="prod-1")
        cp2 = CollectionProduct(collection_id=collection.id, product_id="prod-2")
        session.add(cp1)
        session.add(cp2)
        session.commit()

        # Update count
        collection.update_count(session)
        assert collection.product_count == 2

    def test_is_empty_property(self, session):
        """Test is_empty property."""
        collection = Collection(name="Test Collection")
        assert collection.is_empty

        collection.product_count = 3
        assert not collection.is_empty

        collection.product_count = 0
        assert collection.is_empty

    def test_collection_repr(self, session):
        """Test collection string representation."""
        collection = Collection(name="Test Collection", product_count=5)
        session.add(collection)
        session.commit()

        repr_str = repr(collection)
        assert "Test Collection" in repr_str
        assert "5" in repr_str
        assert collection.id in repr_str


class TestCollectionProduct:
    """Test CollectionProduct model functionality."""

    def test_collection_product_creation(self, session):
        """Test creating a collection product association."""
        collection = Collection(name="Test Collection")
        project = Project(name="Test Project")
        product = Product(project_id=project.id, type="image", file_path="/test.jpg")
        session.add(collection)
        session.add(project)
        session.add(product)
        session.commit()

        cp = CollectionProduct(
            collection_id=collection.id, product_id=product.id, position=3
        )
        session.add(cp)
        session.commit()

        assert cp.collection_id == collection.id
        assert cp.product_id == product.id
        assert cp.position == 3
        assert cp.added_at is not None

    def test_collection_product_defaults(self, session):
        """Test collection product default values."""
        cp = CollectionProduct(collection_id="collection-1", product_id="product-1")
        session.add(cp)
        session.commit()

        assert cp.position == 0
        assert cp.added_at is not None

    def test_move_to_position_method(self, session):
        """Test moving product to new position."""
        cp = CollectionProduct(
            collection_id="collection-1", product_id="product-1", position=5
        )
        session.add(cp)
        session.commit()

        cp.move_to_position(10)
        assert cp.position == 10

    def test_collection_product_repr(self, session):
        """Test collection product string representation."""
        cp = CollectionProduct(
            collection_id="collection-1", product_id="product-1", position=3
        )
        session.add(cp)
        session.commit()

        repr_str = repr(cp)
        assert "collection-1" in repr_str
        assert "product-1" in repr_str
        assert "3" in repr_str

    def test_collection_product_relationships(self, session):
        """Test relationships between collection and product."""
        collection = Collection(name="Test Collection")
        project = Project(name="Test Project")
        product = Product(project_id=project.id, type="image", file_path="/test.jpg")
        session.add(collection)
        session.add(project)
        session.add(product)
        session.commit()

        cp = CollectionProduct(collection_id=collection.id, product_id=product.id)
        session.add(cp)
        session.commit()

        # Test relationship access
        assert cp.collection == collection
        assert cp.product == product

        # Test back-references
        assert cp in collection.products
        assert cp in product.collections

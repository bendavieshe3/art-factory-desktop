"""
Project Management Service.

Handles Project creation, querying, and management operations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func

from ..models import Project, Product, Order
from ..models.database import session_scope


class ProjectServiceError(Exception):
    """Base exception for ProjectService errors."""

    pass


class ProjectNotFoundError(ProjectServiceError):
    """Raised when a project cannot be found."""

    pass


class ProjectValidationError(ProjectServiceError):
    """Raised when project validation fails."""

    pass


class ProjectService:
    """
    Service for managing Project operations.

    Provides CRUD operations, statistics, and management for projects.
    """

    def __init__(self):
        """Initialize the ProjectService."""
        pass

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Name of the project
            description: Optional description
            settings: Optional project settings

        Returns:
            Created Project instance

        Raises:
            ProjectValidationError: If validation fails
            ProjectServiceError: If creation fails
        """
        try:
            # Validate inputs
            if not name or not name.strip():
                raise ProjectValidationError("Project name is required")

            with session_scope() as session:
                # Check for duplicate names
                existing = (
                    session.query(Project)
                    .filter(
                        and_(func.lower(Project.name) == name.lower(), Project.deleted_at.is_(None))
                    )
                    .first()
                )

                if existing:
                    raise ProjectValidationError("A project with this name already exists")

                # Create project
                project = Project(
                    name=name.strip(),
                    description=description.strip() if description else None,
                    status="active",
                )

                # Set settings if provided
                if settings:
                    project.settings = settings

                session.add(project)
                session.commit()
                return project

        except SQLAlchemyError as e:
            raise ProjectServiceError(f"Database error creating project: {str(e)}")

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: ID of the project to retrieve

        Returns:
            Project instance or None if not found
        """
        try:
            with session_scope() as session:
                return (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )
        except SQLAlchemyError:
            return None

    def get_all_projects(
        self,
        include_archived: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Project]:
        """
        Get all projects.

        Args:
            include_archived: Whether to include archived projects
            limit: Maximum number of projects to return
            offset: Number of projects to skip

        Returns:
            List of Project instances
        """
        try:
            with session_scope() as session:
                query = session.query(Project).filter(Project.deleted_at.is_(None))

                if not include_archived:
                    query = query.filter(Project.status != "archived")

                # Order by most recent first
                query = query.order_by(Project.created_at.desc())

                # Apply pagination
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)

                return query.all()

        except SQLAlchemyError:
            return []

    def get_active_projects(self) -> List[Project]:
        """
        Get only active projects.

        Returns:
            List of active Project instances
        """
        try:
            with session_scope() as session:
                return (
                    session.query(Project)
                    .filter(and_(Project.status == "active", Project.deleted_at.is_(None)))
                    .order_by(Project.created_at.desc())
                    .all()
                )
        except SQLAlchemyError:
            return []

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Project]:
        """
        Update a project.

        Args:
            project_id: ID of the project to update
            updates: Dictionary of field updates

        Returns:
            Updated Project instance or None if not found

        Raises:
            ProjectValidationError: If validation fails
            ProjectServiceError: If update fails
        """
        try:
            with session_scope() as session:
                project = (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )

                if not project:
                    return None

                # Validate name if being updated
                if "name" in updates:
                    name = updates["name"]
                    if not name or not name.strip():
                        raise ProjectValidationError("Project name is required")

                    # Check for duplicate names (excluding current project)
                    existing = (
                        session.query(Project)
                        .filter(
                            and_(
                                func.lower(Project.name) == name.lower(),
                                Project.id != project_id,
                                Project.deleted_at.is_(None),
                            )
                        )
                        .first()
                    )

                    if existing:
                        raise ProjectValidationError("A project with this name already exists")

                    updates["name"] = name.strip()

                # Clean description
                if "description" in updates and updates["description"]:
                    updates["description"] = updates["description"].strip()

                # Update fields
                for key, value in updates.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                    else:
                        raise ProjectValidationError(f"Invalid field: {key}")

                session.commit()
                return project

        except SQLAlchemyError as e:
            raise ProjectServiceError(f"Database error updating project: {str(e)}")

    def delete_project(self, project_id: str) -> bool:
        """
        Soft delete a project and all its related data.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if deleted successfully, False if not found

        Raises:
            ProjectServiceError: If deletion fails
        """
        try:
            with session_scope() as session:
                project = (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )

                if not project:
                    return False

                # Soft delete the project (cascade will handle related records)
                project.soft_delete()

                session.commit()
                return True

        except SQLAlchemyError as e:
            raise ProjectServiceError(f"Database error deleting project: {str(e)}")

    def archive_project(self, project_id: str) -> Optional[Project]:
        """
        Archive a project.

        Args:
            project_id: ID of the project to archive

        Returns:
            Updated Project instance or None if not found

        Raises:
            ProjectServiceError: If archiving fails
        """
        return self.update_project(project_id, {"status": "archived"})

    def unarchive_project(self, project_id: str) -> Optional[Project]:
        """
        Unarchive a project (set to active).

        Args:
            project_id: ID of the project to unarchive

        Returns:
            Updated Project instance or None if not found

        Raises:
            ProjectServiceError: If unarchiving fails
        """
        return self.update_project(project_id, {"status": "active"})

    def get_project_statistics(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with project statistics or None if project not found
        """
        try:
            with session_scope() as session:
                project = (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )

                if not project:
                    return None

                # Get counts
                product_count = (
                    session.query(Product)
                    .filter(and_(Product.project_id == project_id, Product.deleted_at.is_(None)))
                    .count()
                )

                order_count = (
                    session.query(Order)
                    .filter(and_(Order.project_id == project_id, Order.deleted_at.is_(None)))
                    .count()
                )

                # Get file size statistics
                size_result = (
                    session.query(func.sum(Product.file_size))
                    .filter(
                        and_(
                            Product.project_id == project_id,
                            Product.deleted_at.is_(None),
                            Product.file_size.isnot(None),
                        )
                    )
                    .scalar()
                )
                total_size = size_result or 0

                # Get latest product creation
                latest_product = (
                    session.query(Product)
                    .filter(and_(Product.project_id == project_id, Product.deleted_at.is_(None)))
                    .order_by(Product.created_at.desc())
                    .first()
                )

                # Get product type breakdown
                type_results = (
                    session.query(Product.type, func.count(Product.id))
                    .filter(and_(Product.project_id == project_id, Product.deleted_at.is_(None)))
                    .group_by(Product.type)
                    .all()
                )

                product_types = {type_name: count for type_name, count in type_results}

                # Get liked products count
                liked_count = (
                    session.query(Product)
                    .filter(
                        and_(
                            Product.project_id == project_id,
                            Product.deleted_at.is_(None),
                            Product.liked == True,
                        )
                    )
                    .count()
                )

                return {
                    "project_id": project_id,
                    "name": project.name,
                    "status": project.status,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                    "product_count": product_count,
                    "order_count": order_count,
                    "total_file_size": total_size,
                    "product_types": product_types,
                    "liked_products": liked_count,
                    "last_generation": (
                        latest_product.created_at.isoformat() if latest_product else None
                    ),
                }

        except SQLAlchemyError:
            return None

    def search_projects(self, query: str, limit: Optional[int] = None) -> List[Project]:
        """
        Search projects by name and description.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Project instances
        """
        try:
            with session_scope() as session:
                search_term = f"%{query}%"
                db_query = (
                    session.query(Project)
                    .filter(
                        and_(
                            Project.deleted_at.is_(None),
                            (
                                Project.name.like(search_term)
                                | Project.description.like(search_term)
                            ),
                        )
                    )
                    .order_by(Project.created_at.desc())
                )

                if limit:
                    db_query = db_query.limit(limit)

                return db_query.all()

        except SQLAlchemyError:
            return []

    def get_featured_products(self, project_id: str) -> List[Product]:
        """
        Get featured products for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of featured Product instances
        """
        try:
            with session_scope() as session:
                project = (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )

                if not project or not project.featured_product_ids:
                    return []

                # Get products in the order they're featured
                featured_products = []
                for product_id in project.featured_product_ids:
                    product = (
                        session.query(Product)
                        .filter(and_(Product.id == product_id, Product.deleted_at.is_(None)))
                        .first()
                    )
                    if product:
                        featured_products.append(product)

                return featured_products

        except SQLAlchemyError:
            return []

    def set_featured_products(self, project_id: str, product_ids: List[str]) -> Optional[Project]:
        """
        Set featured products for a project.

        Args:
            project_id: ID of the project
            product_ids: List of product IDs to feature

        Returns:
            Updated Project instance or None if not found

        Raises:
            ProjectValidationError: If product IDs are invalid
            ProjectServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                project = (
                    session.query(Project)
                    .filter(and_(Project.id == project_id, Project.deleted_at.is_(None)))
                    .first()
                )

                if not project:
                    return None

                # Validate that all product IDs exist and belong to this project
                for product_id in product_ids:
                    product = (
                        session.query(Product)
                        .filter(
                            and_(
                                Product.id == product_id,
                                Product.project_id == project_id,
                                Product.deleted_at.is_(None),
                            )
                        )
                        .first()
                    )
                    if not product:
                        raise ProjectValidationError(f"Invalid product ID: {product_id}")

                # Update featured products
                project.featured_product_ids = product_ids
                session.commit()
                return project

        except SQLAlchemyError as e:
            raise ProjectServiceError(f"Database error setting featured products: {str(e)}")

    def get_project_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all projects.

        Returns:
            Dictionary with project summary statistics
        """
        try:
            with session_scope() as session:
                all_projects = session.query(Project).filter(Project.deleted_at.is_(None)).all()

                active_count = len([p for p in all_projects if p.status == "active"])
                archived_count = len([p for p in all_projects if p.status == "archived"])

                # Get total products across all projects
                total_products = session.query(Product).filter(Product.deleted_at.is_(None)).count()

                # Get total orders across all projects
                total_orders = session.query(Order).filter(Order.deleted_at.is_(None)).count()

                return {
                    "total_projects": len(all_projects),
                    "active_projects": active_count,
                    "archived_projects": archived_count,
                    "total_products": total_products,
                    "total_orders": total_orders,
                }

        except SQLAlchemyError:
            return {"error": "Failed to get project summary"}

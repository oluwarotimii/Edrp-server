from typing import List, Set, Dict, Optional
from sqlalchemy.orm import Session
from functools import wraps

from models.user import User, Role, Permission
from utils.exceptions import UnauthorizedException

class PermissionService:
    """Service for handling permissions and role-based access control"""
    
    @staticmethod
    def get_user_permissions(user: User, db: Session) -> Set[str]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Get permissions from all user roles
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        
        return permissions
    
    @staticmethod
    def has_permission(user: User, permission_name: str, db: Session) -> bool:
        """Check if user has a specific permission"""
        user_permissions = PermissionService.get_user_permissions(user, db)
        return permission_name in user_permissions
    
    @staticmethod
    def has_any_permission(user: User, permission_names: List[str], db: Session) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = PermissionService.get_user_permissions(user, db)
        return any(perm in user_permissions for perm in permission_names)
    
    @staticmethod
    def has_all_permissions(user: User, permission_names: List[str], db: Session) -> bool:
        """Check if user has all of the specified permissions"""
        user_permissions = PermissionService.get_user_permissions(user, db)
        return all(perm in user_permissions for perm in permission_names)
    
    @staticmethod
    def assign_role_to_user(user: User, role: Role, db: Session) -> None:
        """Assign a role to a user"""
        if role not in user.roles:
            user.roles.append(role)
            db.commit()
    
    @staticmethod
    def remove_role_from_user(user: User, role: Role, db: Session) -> None:
        """Remove a role from a user"""
        if role in user.roles:
            user.roles.remove(role)
            db.commit()
    
    @staticmethod
    def assign_permission_to_role(role: Role, permission: Permission, db: Session) -> None:
        """Assign a permission to a role"""
        if permission not in role.permissions:
            role.permissions.append(permission)
            db.commit()
    
    @staticmethod
    def remove_permission_from_role(role: Role, permission: Permission, db: Session) -> None:
        """Remove a permission from a role"""
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.commit()
    
    @staticmethod
    def create_default_permissions(db: Session) -> None:
        """Create default system permissions"""
        default_permissions = [
            # School management
            ("schools:view", "View school information", "schools", "view"),
            ("schools:update", "Update school information", "schools", "update"),
            ("schools:manage", "Manage school settings", "schools", "manage"),
            ("schools:view_all", "View all schools (admin)", "schools", "view_all"),
            ("schools:update_all", "Update any school (admin)", "schools", "update_all"),
            ("schools:approve", "Approve schools (admin)", "schools", "approve"),
            
            # User management
            ("users:view", "View users", "users", "view"),
            ("users:create", "Create users", "users", "create"),
            ("users:update", "Update users", "users", "update"),
            ("users:delete", "Delete users", "users", "delete"),
            ("users:approve", "Approve users", "users", "approve"),
            
            # Role management
            ("roles:view", "View roles", "roles", "view"),
            ("roles:create", "Create roles", "roles", "create"),
            ("roles:update", "Update roles", "roles", "update"),
            ("roles:delete", "Delete roles", "roles", "delete"),
            ("roles:manage_permissions", "Manage role permissions", "roles", "manage_permissions"),
            
            # Permission management
            ("permissions:view", "View permissions", "permissions", "view"),
            ("permissions:create", "Create permissions", "permissions", "create"),
            
            # Student management
            ("students:view", "View students", "students", "view"),
            ("students:create", "Create students", "students", "create"),
            ("students:update", "Update students", "students", "update"),
            ("students:delete", "Delete students", "students", "delete"),
            ("students:manage_parents", "Manage student-parent relationships", "students", "manage_parents"),
            ("students:manage_custom_fields", "Manage student custom fields", "students", "manage_custom_fields"),
            ("students:update_status", "Update student status", "students", "update_status"),
            
            # Teacher management
            ("teachers:view", "View teachers", "teachers", "view"),
            ("teachers:create", "Create teachers", "teachers", "create"),
            ("teachers:update", "Update teachers", "teachers", "update"),
            ("teachers:delete", "Delete teachers", "teachers", "delete"),
            ("teachers:assign", "Assign teachers to subjects/classes", "teachers", "assign"),
            ("teachers:unassign", "Remove teacher assignments", "teachers", "unassign"),
            ("teachers:unassign_all", "Remove all teacher assignments", "teachers", "unassign_all"),
            ("teachers:update_status", "Update teacher status", "teachers", "update_status"),
            
            # Academic management
            ("departments:view", "View departments", "departments", "view"),
            ("departments:create", "Create departments", "departments", "create"),
            ("departments:update", "Update departments", "departments", "update"),
            ("departments:delete", "Delete departments", "departments", "delete"),
            
            ("classes:view", "View classes", "classes", "view"),
            ("classes:create", "Create classes", "classes", "create"),
            ("classes:update", "Update classes", "classes", "update"),
            ("classes:delete", "Delete classes", "classes", "delete"),
            
            ("subjects:view", "View subjects", "subjects", "view"),
            ("subjects:create", "Create subjects", "subjects", "create"),
            ("subjects:update", "Update subjects", "subjects", "update"),
            ("subjects:delete", "Delete subjects", "subjects", "delete"),
            
            ("academic_sessions:view", "View academic sessions", "academic", "view_sessions"),
            ("academic_sessions:create", "Create academic sessions", "academic", "create_sessions"),
            ("academic_sessions:update", "Update academic sessions", "academic", "update_sessions"),
            ("academic_sessions:delete", "Delete academic sessions", "academic", "delete_sessions"),
            
            ("terms:view", "View terms", "academic", "view_terms"),
            ("terms:create", "Create terms", "academic", "create_terms"),
            ("terms:update", "Update terms", "academic", "update_terms"),
            ("terms:delete", "Delete terms", "academic", "delete_terms"),
            
            # Attendance management
            ("attendance:view", "View attendance", "attendance", "view"),
            ("attendance:take", "Take attendance", "attendance", "take"),
            ("attendance:update", "Update attendance", "attendance", "update"),
            ("teacher_attendance:view", "View teacher attendance", "attendance", "view_teacher"),
            ("teacher_attendance:manage", "Manage teacher attendance", "attendance", "manage_teacher"),
            
            ("locations:view", "View authentic locations", "locations", "view"),
            ("locations:create", "Create authentic locations", "locations", "create"),
            ("locations:update", "Update authentic locations", "locations", "update"),
            ("locations:delete", "Delete authentic locations", "locations", "delete"),
            
            # Assessment management
            ("assessment_schemes:view", "View assessment schemes", "assessments", "view_schemes"),
            ("assessment_schemes:create", "Create assessment schemes", "assessments", "create_schemes"),
            ("assessment_schemes:update", "Update assessment schemes", "assessments", "update_schemes"),
            ("assessment_schemes:delete", "Delete assessment schemes", "assessments", "delete_schemes"),
            ("assessment_schemes:manage_components", "Manage scheme components", "assessments", "manage_components"),
            ("assessment_schemes:assign", "Assign schemes to classes/subjects", "assessments", "assign_schemes"),
            
            ("grading_scales:view", "View grading scales", "assessments", "view_scales"),
            ("grading_scales:create", "Create grading scales", "assessments", "create_scales"),
            ("grading_scales:update", "Update grading scales", "assessments", "update_scales"),
            ("grading_scales:delete", "Delete grading scales", "assessments", "delete_scales"),
            
            ("assessments:view", "View assessments", "assessments", "view"),
            ("assessments:create", "Create assessments", "assessments", "create"),
            ("assessments:update", "Update assessments", "assessments", "update"),
            ("assessments:delete", "Delete assessments", "assessments", "delete"),
            ("assessments:publish", "Publish/withhold assessment results", "assessments", "publish"),
            
            ("scores:view", "View scores", "assessments", "view_scores"),
            ("scores:create", "Create scores", "assessments", "create_scores"),
            ("scores:update", "Update scores", "assessments", "update_scores"),
            ("scores:delete", "Delete scores", "assessments", "delete_scores"),
            
            ("reports:view", "View reports", "reports", "view"),
            ("reports:generate", "Generate reports", "reports", "generate"),
            
            # Fee management
            ("fee_types:view", "View fee types", "fees", "view_types"),
            ("fee_types:create", "Create fee types", "fees", "create_types"),
            ("fee_types:update", "Update fee types", "fees", "update_types"),
            ("fee_types:delete", "Delete fee types", "fees", "delete_types"),
            
            ("student_fees:view", "View student fees", "fees", "view_student_fees"),
            ("student_fees:create", "Create student fees", "fees", "create_student_fees"),
            ("student_fees:update", "Update student fees", "fees", "update_student_fees"),
            ("student_fees:delete", "Delete student fees", "fees", "delete_student_fees"),
            
            ("payments:view", "View payments", "fees", "view_payments"),
            ("payments:create", "Create payments", "fees", "create_payments"),
            ("payments:update", "Update payments", "fees", "update_payments"),
            ("payments:delete", "Delete payments", "fees", "delete_payments"),
            
            # Communication
            ("messages:view", "View messages", "communication", "view_messages"),
            ("messages:create", "Create messages", "communication", "create_messages"),
            ("messages:update", "Update messages", "communication", "update_messages"),
            ("messages:delete", "Delete messages", "communication", "delete_messages"),
            
            ("behavior_reports:view", "View behavior reports", "communication", "view_reports"),
            ("behavior_reports:create", "Create behavior reports", "communication", "create_reports"),
            ("behavior_reports:update", "Update behavior reports", "communication", "update_reports"),
            ("behavior_reports:delete", "Delete behavior reports", "communication", "delete_reports"),
            
            # Happenings
            ("happenings:view", "View happenings", "happenings", "view"),
            ("happenings:create", "Create happenings", "happenings", "create"),
            ("happenings:update", "Update happenings", "happenings", "update"),
            ("happenings:delete", "Delete happenings", "happenings", "delete"),
            ("happenings:publish", "Publish happenings", "happenings", "publish"),
            ("happenings:view_unpublished", "View unpublished happenings", "happenings", "view_unpublished"),
            ("happenings:manage_categories", "Manage happening categories", "happenings", "manage_categories"),
            ("happenings:view_statistics", "View happening statistics", "happenings", "view_statistics"),
            
            # Timetable
            ("periods:view", "View periods", "timetable", "view_periods"),
            ("periods:create", "Create periods", "timetable", "create_periods"),
            ("periods:update", "Update periods", "timetable", "update_periods"),
            ("periods:delete", "Delete periods", "timetable", "delete_periods"),
            
            ("timetables:view", "View timetables", "timetable", "view"),
            ("timetables:create", "Create timetable entries", "timetable", "create"),
            ("timetables:update", "Update timetable entries", "timetable", "update"),
            ("timetables:delete", "Delete timetable entries", "timetable", "delete"),
            
            # Admissions
            ("admissions:view", "View applications", "admissions", "view"),
            ("admissions:create", "Create applications", "admissions", "create"),
            ("admissions:update", "Update applications", "admissions", "update"),
            ("admissions:update_status", "Update application status", "admissions", "update_status"),
            ("admissions:approve", "Approve applications", "admissions", "approve"),
            ("admissions:upload_documents", "Upload application documents", "admissions", "upload_documents"),
            
            # Admin
            ("audit_logs:view", "View audit logs", "admin", "view_logs"),
            ("subscription_plans:view", "View subscription plans", "admin", "view_plans"),
            ("subscription_plans:create", "Create subscription plans", "admin", "create_plans"),
            ("subscription_plans:update", "Update subscription plans", "admin", "update_plans"),
            ("subscription_plans:manage_features", "Manage plan features", "admin", "manage_features"),
            ("analytics:view", "View analytics", "admin", "view_analytics"),
            ("admin:view_statistics", "View system statistics", "admin", "view_statistics"),
            ("admin:view_system_health", "View system health", "admin", "view_system_health"),
        ]
        
        for name, description, module, action in default_permissions:
            existing = db.query(Permission).filter(Permission.name == name).first()
            if not existing:
                permission = Permission(
                    name=name,
                    description=description,
                    module=module,
                    action=action
                )
                db.add(permission)
        
        db.commit()
    
    @staticmethod
    def create_default_roles(db: Session) -> None:
        """Create default system roles"""
        # Create default roles with their permissions
        default_roles = {
            "super_admin": {
                "description": "Super administrator with all permissions",
                "permissions": "*"  # All permissions
            },
            "school_admin": {
                "description": "School administrator",
                "permissions": [
                    "schools:view", "schools:update", "schools:manage",
                    "users:view", "users:create", "users:update", "users:approve",
                    "roles:view", "roles:create", "roles:update", "roles:manage_permissions",
                    "students:*", "teachers:*", "departments:*", "classes:*", "subjects:*",
                    "academic_sessions:*", "terms:*", "attendance:*", "locations:*",
                    "assessment_schemes:*", "grading_scales:*", "assessments:*", "scores:*",
                    "fee_types:*", "student_fees:*", "payments:*",
                    "messages:*", "behavior_reports:*", "happenings:*",
                    "periods:*", "timetables:*", "admissions:*"
                ]
            },
            "teacher": {
                "description": "Teacher role",
                "permissions": [
                    "students:view", "attendance:take", "attendance:view",
                    "assessments:view", "assessments:create", "assessments:update",
                    "scores:view", "scores:create", "scores:update",
                    "messages:view", "messages:create", "behavior_reports:create",
                    "timetables:view", "happenings:view"
                ]
            },
            "student": {
                "description": "Student role",
                "permissions": [
                    "assessments:view", "scores:view", "messages:view", "messages:create",
                    "happenings:view", "timetables:view"
                ]
            },
            "parent": {
                "description": "Parent/Guardian role",
                "permissions": [
                    "students:view", "attendance:view", "assessments:view", "scores:view",
                    "student_fees:view", "payments:view", "messages:view", "messages:create",
                    "behavior_reports:view", "happenings:view"
                ]
            },
            "accountant": {
                "description": "School accountant",
                "permissions": [
                    "fee_types:*", "student_fees:*", "payments:*",
                    "students:view", "reports:view"
                ]
            }
        }
        
        for role_name, role_data in default_roles.items():
            existing_role = db.query(Role).filter(Role.name == role_name).first()
            if not existing_role:
                role = Role(
                    name=role_name,
                    description=role_data["description"],
                    is_system_role=True,
                    school_id=1  # System roles belong to a default school
                )
                db.add(role)
                db.flush()
                
                # Assign permissions
                if role_data["permissions"] == "*":
                    # Assign all permissions
                    all_permissions = db.query(Permission).all()
                    role.permissions.extend(all_permissions)
                else:
                    # Assign specific permissions
                    for perm_pattern in role_data["permissions"]:
                        if perm_pattern.endswith("*"):
                            # Wildcard permission - assign all permissions in module
                            module_prefix = perm_pattern[:-1]
                            matching_perms = db.query(Permission).filter(
                                Permission.name.like(f"{module_prefix}%")
                            ).all()
                            role.permissions.extend(matching_perms)
                        else:
                            # Specific permission
                            permission = db.query(Permission).filter(
                                Permission.name == perm_pattern
                            ).first()
                            if permission:
                                role.permissions.append(permission)
        
        db.commit()

def require_permission(permission_name: str):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is a placeholder - actual implementation would depend on
            # how current_user is passed to the function
            # In FastAPI, this would typically be handled by dependencies
            pass
        return wrapper
    return decorator

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Violation(db.Model):
    __tablename__ = 'violations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_number = db.Column(db.String(20), nullable=False, index=True)
    violation_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    violation_date = db.Column(db.Date, nullable=False)
    fine_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), nullable=False, default='Unpaid')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'violation_type': self.violation_type,
            'location': self.location,
            'violation_date': self.violation_date.strftime('%Y-%m-%d') if self.violation_date else '',
            'fine_amount': self.fine_amount,
            'payment_status': self.payment_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Violation #{self.id} {self.vehicle_number} - {self.violation_type} ({self.payment_status})>'

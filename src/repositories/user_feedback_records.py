#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : user_feedback_records.py

from sqlalchemy.ext.asyncio import AsyncSession

class UserFeedbackRecordsRepository:

    def __init__(self, db: AsyncSession):
        self.session = db

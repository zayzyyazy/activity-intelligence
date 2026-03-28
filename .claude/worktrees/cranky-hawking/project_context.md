# Project name
Personal Work OS

# Goal
Build a local AI-assisted system that tracks what I say I’m doing and what I’m actually doing on my laptop, then turns that into structured insight.

# Stack
Python, SQLite, ActivityWatch, file monitoring

# Current task
Connect ActivityWatch and file activity into the SQLite database.
I’m building a Personal Work OS — a local, AI-powered system that combines manual activity logging, passive laptop tracking (via ActivityWatch), and structured work items into one unified SQLite-based system that not only records what I do but understands it and helps me improve it. I started with logging and AI classification, then added work items, daily and weekly reports, and CSV exports, and now I’m in the next phase where I’m connecting passive activity (what my laptop shows I’m doing) with my logged intent to detect alignment and mismatches. At this exact step, I’ve already integrated passive data and built an alignment check into the daily report, and I’m now validating and refining how the AI uses that signal to explicitly call out mismatches and suggest improvements — moving the system from tracking behavior to actually analyzing and guiding it.

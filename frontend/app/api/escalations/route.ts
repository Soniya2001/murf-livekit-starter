import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

// Locate database file
const dbPath = path.resolve(process.cwd(), '../backend/finbuddy_memory.db');

async function getDb() {
  return open({
    filename: dbPath,
    driver: sqlite3.Database,
  });
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const status = searchParams.get('status');
    const db = await getDb();
    
    let query = `
      SELECT reference_id, user_id, caller_name, issue_summary, what_happened, agent_checks, urgency, language, preferred_follow_up, status, created_at
      FROM escalation_requests
    `;
    const params: any[] = [];
    
    if (status) {
      query += ' WHERE status = ?';
      params.push(status);
    }
    
    query += ' ORDER BY created_at DESC';
    
    const rows = await db.all(query, params);
    await db.close();
    
    return NextResponse.json({ success: true, escalations: rows });
  } catch (error: any) {
    console.error('API GET escalations failed:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { reference_id, status } = body;
    
    if (!reference_id || !status) {
      return NextResponse.json({ success: false, error: 'Missing reference_id or status' }, { status: 400 });
    }
    
    const db = await getDb();
    const result = await db.run(
      'UPDATE escalation_requests SET status = ? WHERE reference_id = ?',
      [status, reference_id]
    );
    await db.close();
    
    if (result.changes && result.changes > 0) {
      return NextResponse.json({ success: true });
    } else {
      return NextResponse.json({ success: false, error: 'Escalation request not found' }, { status: 404 });
    }
  } catch (error: any) {
    console.error('API POST escalations failed:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

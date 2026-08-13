import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

export const dynamic = 'force-dynamic';

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
    const db = await getDb();
    
    // Get total calls
    const totalRow = await db.get("SELECT COUNT(*) as count FROM call_outcomes");
    const total_calls = totalRow ? totalRow.count : 0;
    
    // Get successful calls
    const successRow = await db.get("SELECT COUNT(*) as count FROM call_outcomes WHERE outcome = 'SUCCESS'");
    const successful_calls = successRow ? successRow.count : 0;
    
    // Get failed calls
    const failedRow = await db.get("SELECT COUNT(*) as count FROM call_outcomes WHERE outcome = 'FAILED'");
    const failed_calls = failedRow ? failedRow.count : 0;
    
    const success_rate = total_calls > 0 ? Math.round((successful_calls / total_calls) * 100) : 0;
    
    // Additional info: recent calls (limit to 10)
    const recent_calls = await db.all(`
      SELECT co.call_id, co.user_id, c.name AS caller_name, co.call_type, co.outcome, co.duration_seconds, co.language, co.scheme_name, co.success_reason, strftime('%Y-%m-%dT%H:%M:%SZ', co.created_at) as created_at 
      FROM call_outcomes co
      LEFT JOIN callers c ON co.user_id = c.user_id
      ORDER BY co.created_at DESC 
      LIMIT 10
    `);
    
    // Success reason breakdown
    const reason_breakdown = await db.all(`
      SELECT success_reason, COUNT(*) as count 
      FROM call_outcomes 
      WHERE outcome = 'SUCCESS'
      GROUP BY success_reason
    `);
    
    // Language distribution
    const language_distribution = await db.all(`
      SELECT language, COUNT(*) as count 
      FROM call_outcomes 
      GROUP BY language
    `);
    
    // Call type distribution
    const call_types = await db.all(`
      SELECT call_type, COUNT(*) as count 
      FROM call_outcomes 
      GROUP BY call_type
    `);
    
    await db.close();
    
    return NextResponse.json({
      success: true,
      total_calls,
      successful_calls,
      failed_calls,
      success_rate,
      recent_calls,
      reason_breakdown,
      language_distribution,
      call_types
    });
  } catch (error: any) {
    console.error('API GET call-analytics failed:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

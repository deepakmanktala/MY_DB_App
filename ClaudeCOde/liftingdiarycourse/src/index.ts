import 'dotenv/config';
import { drizzle } from 'drizzle-orm/neon-http';
import { eq } from 'drizzle-orm';
import { exercises, workouts, workoutExercises, sets } from './db/schema';

const db = drizzle(process.env.DATABASE_URL!);

async function main() {
  // 1. Insert a global exercise
  const [exercise] = await db
    .insert(exercises)
    .values({ name: 'Bench Press', muscleGroup: 'chest' })
    .onConflictDoNothing()
    .returning();

  console.log('Exercise created:', exercise ?? 'already exists');

  // Fetch it in case it already existed
  const [existingExercise] = await db
    .select()
    .from(exercises)
    .where(eq(exercises.name, 'Bench Press'));

  console.log('Using exercise:', existingExercise);

  // 2. Start a workout session
  const [workout] = await db
    .insert(workouts)
    .values({ clerkUserId: 'test_user_123', title: 'Morning Push Day' })
    .returning();

  console.log('Workout started:', workout);

  // 3. Add the exercise to the workout
  const [workoutExercise] = await db
    .insert(workoutExercises)
    .values({ workoutId: workout.id, exerciseId: existingExercise.id, orderIndex: 0 })
    .returning();

  console.log('Exercise added to workout:', workoutExercise);

  // 4. Log some sets
  const setData: (typeof sets.$inferInsert)[] = [
    { workoutExerciseId: workoutExercise.id, setNumber: 1, reps: 10, weightKg: '60.00', rpe: '7.0' },
    { workoutExerciseId: workoutExercise.id, setNumber: 2, reps: 8,  weightKg: '65.00', rpe: '8.0' },
    { workoutExerciseId: workoutExercise.id, setNumber: 3, reps: 6,  weightKg: '70.00', rpe: '9.0' },
  ];

  const insertedSets = await db.insert(sets).values(setData).returning();
  console.log('Sets logged:', insertedSets);

  // 5. Complete the workout
  await db
    .update(workouts)
    .set({ completedAt: new Date() })
    .where(eq(workouts.id, workout.id));

  console.log('Workout completed!');

  // 6. Query all sets for this workout
  const allSets = await db.select().from(sets).where(eq(sets.workoutExerciseId, workoutExercise.id));
  console.log('All sets for workout:', allSets);

  // 7. Cleanup — delete the test workout (cascades to workout_exercises and sets)
  await db.delete(workouts).where(eq(workouts.id, workout.id));
  console.log('Test workout deleted (cascade cleaned up exercises + sets)');
}

main();
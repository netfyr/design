import { enhance } from '../src/components.js';
import { initializeGallery } from '../gallery-shell.js';
import { initializePreviews } from './previews.js';
import { initializeRecordings } from './recordings.js';

enhance();
initializeGallery();
initializeRecordings();
await initializePreviews();
document.documentElement.dataset.galleryReady = 'true';

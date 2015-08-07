package deeplab.MetroPictures;

import ddf.minim.*;

public class MPPAudioPad {
	MPPCore parent;
	
	Minim minim;
	AudioPlayer player;
	AudioPlayer dtmf;
	
	AudioInput audio_in;
	AudioRecorder recorder;
		
	public MPPAudioPad(MPPCore parent) {
		this.parent = parent;
		minim = new Minim(this.parent);
	}
	
	public boolean playTone(String key) {
		System.out.println("playing tone " + key);
		
		if(dtmf != null && dtmf.isPlaying()) {
			dtmf.close();
		}
		
		dtmf = minim.loadFile(parent.media_dir + "dtmf/DTMF-" + key + ".mp3");
		dtmf.play();
		
		return true;
	}
	
	public int play(String src) {
		System.out.println("playing file from " + src);
		
		if(dtmf != null && dtmf.isPlaying()) {
			dtmf.close();
		}
		
		player = minim.loadFile(parent.media_dir + src);
		player.play();
		
		return player.length();
	}
	
	public boolean startRecording(String dst) {
		if(recorder != null) {
			if(recorder.isRecording()) {
				return false;
			}
			
			recorder = null;
		}
		
		if(audio_in == null) {
			audio_in = minim.getLineIn(Minim.STEREO, 2048);
		}
		
		recorder = minim.createRecorder(audio_in, parent.media_dir + dst);
		recorder.beginRecord();
		
		return recorder.isRecording();
	}
	
	public boolean stopRecording() {
		if(recorder == null || !recorder.isRecording()) {
			return false;
		}
		
		recorder.endRecord();
		recorder.save();
		return !recorder.isRecording();
	}

	public void draw() {}
}

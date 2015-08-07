package deeplab.MetroPictures;

import processing.core.*;

import java.util.Arrays;

import org.json.JSONObject;

import deeplab.MetroPictures.handlers.MPPHandlers;
import deeplab.MetroPictures.handlers.MPPServer;

@SuppressWarnings("serial")
public class MPPCore extends PApplet implements MPPHandlers {
	MPPServer server;
	protected MPPAudioPad audio_pad;
	
	public String media_dir;
	
	final static String[] dtmf = new String[] {"1", "2", "3", "4", "5", "6", 
		"7", "8", "9", "0", "s", "p", "d", "b", "r"};
	
	public void setup() {
		String[] user_dir = System.getProperty("user.dir").split("/");
		media_dir = String.join("/", Arrays.copyOfRange(user_dir, 0, user_dir.length - 1)) + "/core/media/";
		
		System.out.println(media_dir);
		
		server = new MPPServer(this);
		audio_pad = new MPPAudioPad(this);
		
		server.start();
	}
	
	public void draw() {
		server.draw();
		audio_pad.draw();
	}
	
	public void keyReleased() {
		// this method is just for testing on keyboard...
		
		if(key == 'x') {
			server.stop();
		} else if(key == 'w') {
			server.start();
		} else if(Arrays.asList(dtmf).contains(String.valueOf(key))) {
			audio_pad.playTone(String.valueOf(key));
		}

		System.out.println("Server running? " + server.getStatus());	
	}

	@Override
	public JSONObject onCommand(JSONObject command) {
		System.out.println(command.toString());
		boolean result = false;
		
		JSONObject json = new JSONObject();
		
		if(command.has("check_status")) {
			result = server.getStatus();
		}
		
		if(command.has("press") && Arrays.asList(dtmf).contains(command.getString("press"))) {
			result = audio_pad.playTone(command.getString("press"));
		}
		
		if(command.has("play")) {
			result = true;
			json.put("play_length", audio_pad.play(command.getString("play")));
		}
		
		if(command.has("start_recording")) {
			result = audio_pad.startRecording(command.getString("start_recording"));
		}
		
		if(command.has("stop_recording")) {
			result = audio_pad.stopRecording();
		}
		
		json.put("response", result);
		System.out.println(json.toString());
		
		return json;
	}
}

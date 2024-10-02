![image](https://github.com/Alucard24/Rope/releases/download/splash/splash_next.png)

Next(Stable)-1.1.03

New Features:
Imported and updated @Hans's changes to work on CUDA tensors without passing through the CPU, except for the JPEG compression feature.
Added simplify_dfm_onnx.py script to simplify DFM models, enabling them to work with TensorRT/TensorRT-Engine providers, even for those with morph_value:0 as an input parameter.
(I.E: "python tools\simplify_dfm_onnx.py ./dfl_models ./dfl_models/patched --extension .dfm --dynamic_input morph_value:0")
Add functions to work on torch tensor.
Lay the groundwork for supporting new providers.
Ready for Rope-Next-Portable!

Improvements:
Optimized DFL models to work directly on CUDA tensors without passing through the CPU. This significantly increases DFL model inference performance.
Improve performance for histogram_matching_DFL_Orig and histogram_matching_DFL_test functions. Now they work without permute operation.
Optimize DFL Model rct function.
Optimize the apply_face_parser function for performance.
Optimize CLIPSwitch inference to work entirely on CUDA tensors or CPU tensors.

Changes:
Make tensor options configurable through the trt_ep_options variable.
Add trt_max_workspace_size property to trt_ep_options variable.
Update requirements. Add onnxsimplify.
Update requirements: Add kornia package.
Add two functions in order to use kornia.geometry.transform.warpaffine.
Change the faceparser model with the updated one. Big Thanks to @yakhyo
Remove useless code.
Move DFMModel, FaceEditor, FaceLandmarks and TensorRTPredictor classes into the proper files.
Remove Rope-cu118.bat and Rope-cu124.bat files.
Update requirements. Add requests package.

Bug Fixes:
Fix autoswap. Big Thanks to @mister.nobody.1234
Fix issues for histogram_matching_DFL_Orig and histogram_matching_DFL_test functions.
Fix for an issue on 2nd Restorer when active.
Fix an issue when providers setting is set to CPU

Next(Stable)-1.1.02

Changes:
Apply edit faces only if named parameters are not as default.
Migrate to TensorRT 10.4.0.
Update onnxruntime-gpu requirements_cu124 to 1.19.2 version.
Update requirements and requirements_cu124 to support TensorRT 10.4.0.
TensorRT 10.4.0 binary files need to be installed following the guide on NVIDIA official site.

Bug Fixes:
Use dtype=object for kpss to manage elements of variable length.

Next(Stable)-1.1.01
Contributors: @argenspin

New Features:
Merge latest @argenspin updates. Big thanks to him.

Changes:
Update requirements: Upgrade torch to 2.4.1 version.
Add thread synchronization for TensorRT-Engine with Settings.
Remove useless syncvec variable. Use instead torch.cuda.synchronize() function.

Bug Fixes:
Better TensorRT-Engine models detection.
kpss variable must be an array not a list.
Always add to kpss, regardless of the length of landmark_kpss.

Next(Stable)-1.1.00
Contributors: @KwaiVGI, @warmshao, @argenspin

New Features:
Added new FaceEditor functionality based on the official LivePortrait repository.
Added new TensorRT Engine provider to increase performance for FaceEditor functionality.
Added new 203-point facial landmark detector.
Merge all DFL implementation changes made by @argenspin. Big Thanks to him.

Improvements:
Improved Show Landmarks functionality to display all keypoints when enabled and a landmark detector is selected. Landmarks Position Adjustments will always show 5 keypoints as it is based on them.
Improved slider min/max values for Face ID settings in Landmarks Position Adjustments and FaceEditor functionalities. Now, the min and max values are applied for each frame.
Improved Face Detector functions to return 5 keypoints and 68/98/106/203/478 keypoints depending on the selected landmarks.
Increased performance of some functions in the FaceUtil library.
Inswapper 128: Improves memory efficiency and performance in image tiling.
Improves memory efficiency and performance in enhance frame :image tiling.
Improves VRAM_Indicator class in order to avoid potential issues.
Refactored and fixed TensorRTPredictor class. Added synchronized predict method. Now ready to work asynchronously without any issues.

Changes:
Cleaned code by removing unnecessary comments.
Update requirements for CUDA 11.8 and CUDA 12.4.
Update .gitignore file.
Added liveportrait_onnx subdirectory to contain new FaceEditor models.
Rename LandmarksPositionAdjSwitch display text into 5 Landmarks Position Adjustments.
Landmark Position Adjustments: Code Refactored.
Update splash logo, github repository, discord channel and donation links.
Update README.md file.

Bug Fixes:
Fixed an issue with Show Landmarks and Landmarks Position Adjustments functionalities. Now, changes to Input Face Adjustments will be reflected in both Show Landmarks and Landmarks Position Adjustments.
Temporary fix in problem selecting camera backend.
Fix for an issue on auto_swap function.
Fix an issue in swap_edit_face_core when 203 landmark model is not initialized.

Pearl-0.8.22
Contributors: @mz28k

Changes:
Terminate audio process if active when closing Rope. | 1535e18
Terminate the audioprocess when needed if it is active. | 088ac01
Revert optimized UI loop. Code refactored from @mz28k’s source. | 1babee9

Bug Fixes:
Fix for audio process finding the current frame. | 18851f4

Pearl-0.8.21
Contributors: @mz28k

New Features:
Added time management for video. | cb69228

Improvements:
Added requirements for CUDA 12.4. | 8337c5a
Update .gitignore. | e36944c
Update requirements for CUDA 11.8. | 842519a
Optimized UI loop. Code refactored from @mz28k’s source. | 441544d
Added batch files to run Rope on cuda 11.8 or cuda 12.4. | 5ac81c6
Removed unused apply_bg_face_parser fuction code. | b418c3e

Bug Fixes:
Fixed issue on resnet50 function initializing self.anchors variable due to clear_mem function execution. | dac3335

Pearl-0.8.20
Contributors: @argenspin

Features:
5e1e580
Adds the “Restore Eyes” and “Restore Mouth” functionality, allowing the shape and size of the mask to be defined. It is now possible to see changes in real-time via “Show Mask.” This feature is based on the commit “eyes and mouth restore now use a circular mask” by @argenspin.
Adds the functionality to sort the display of parameters visible or invisible through the configuration interace.
Adds the functionality to sort the display of parameters through the configuration interface.
Adds the ability to save, load, and reset the visibility and sorting configuration of parameters.
 The file name that will be loaded at Rope's startup should be: "custom_parameters_visibility.json"

Improvements:
Ensure the elements of the tensor are stored in a continuous block of memory, without any gaps or interruptions. | c881370
Improves the loading performance of Rope.

Changes:
Changes the name of the parameters file that is loaded at Rope's startup
 from "saved_parameters.json" to "startup_parameters.json."
Changes the structure of the parameters file, adding the configuration type.
 Any previously saved parameters files are no longer compatible.

Bug Fixes:
Fixed the issues on CUDA 12.4 using FaceParser and/or Restorer in reference mode.
Fixed issue about loading wrong or missing parameters in saved parameters file. | eb7c72a
Fixed an issue with the resizing of the vertical scroll bar when a user switches
 between Video mode and Image mode, and vice versa.
Fixed the issue where certain parts of the interface were not visible during window movement or resizing in Rope.

Pearl-0.8.17 – 8.19
Contributors: n/a

Features:
Tab saves slider textbox input (Merge pull request #4 from aonmkugs/slider-tab-input.) | 64d8214
Support loading old markers json files. (Merge pull request #5 from aonmkugs/load-old-json-formats.) | 147abeb

Improvements:
Optimize UI loop (Merge pull request #6 from mz28k/m-next.) | 8f519f3
Optimize trans_points2d and trans_points3d functions for performance. | 2090f2a

Bug Fixes:
Fix for audio process. Force to kill ffplay and subprocess that remains active. | b176183
Revert “Merge pull request #6 from mz28k/m-next. | 178563f

Pearl-0.8.7 – 8.15
Contributors: n/a

Features:
Add Frame Blend slider setting. | 6d4d8b8
Add support for RealEsr-General-x4v3 model. | cf1acb6
Add support for DDColor and DDColor colorizer models. | b41968c
Tab saves slider textbox input. | 3c45967
Support loading old markers json files. | 1f19bef

Improvements:
Cleaning code. Remove superfluous TAB, spaces and carriage return characters. | dae2fbb
Add script for cleaning code. | c932850
Optimize loop. | 7b862d4
Make slider being more responsive. | 076bafe

Minor Fixes:
Fixed typo. Thanks to @kraibse. | cc4a62b

Pearl-0.8.5 – 8.6
Contributors: n/a

Features:
Add Frame Upscaler functionality.  | e48244a
Added support for the following Frame Enhancer models:
4x-UltraSharp
BSRGAN x4
BSRGAN x2
Real ESRGAN x4 Plus
Real ESRGAN x2 Plus
DeOldify Video
DeOldify Stable
DeOldify Artistic
4x UltraMix Smooth
Added support for the following Face Enhancer model:
Restore Former ++

Improvements: 
Implement TextSelectionComboBox control. | 69b826c

Changes:
Change the name for some settings.
Re-organize some settings visualization in a proper way.

Pearl v0.7.15 – 7.31
Contributors: @Asmirald , @argenspin 

Features:
Added support for DFL XSeg v2 model. I personally converted last updated and trained XSeg v2 model.  | f88bd03
Implemented DFL XSeg size. | 0bb691e
Implemented the possibility to Save and Load various parameters files. Thanks to Asmirald. | baa809d
Implemented VQFR v2 face restorer model. | 8ba1a68
Updates for Rope-Live:
(ca43030)
Added option to select Webcam FPS.
Added option to select maximum number of Webcams to detect (set to 0 to disable webcam detection).
Added back the Eyes and Mouth restoration mod v1.1 features
Added webcam fps selection and some other changes. Thanks to @argenspin. | c37c1cb

Improvements:
Ensured that a tensor has contiguous memory. | d020d30
Updated XSeg model v2 trained by myself and based on latest Shennong 256 XSEG one. | c3ca6a3
Updated XSeg model (Milx version). Big thanks to him. | 8a1a6b9
Improved pad_image_by_size function. | 5de1c35

Changes:
Changed Sides Border Distance in Left and Right Border distance. | d1ab044

Pearl v0.7.2 - 7.13
Contributors: @argenspin , @Doctor_Dentist t, @Hans , @coofly, @Asmirald 

Features:
Added more face attributes to the Face Parser. | 6f0f74c
Added Auto Rotation functionality for all Face Detectors. When active, frames will be rotated during the face detection in order to improve detection accuracy. | 4e6e19d
Added support for TensorRT provider and added the functionality to switch Providers Priority in realtime. Updated requirements.txt in order to support TensorRT without downloading TensorRT 8.6 GA package and change the PATH environment. | 11d24a2
Improve Color Adjustments functionality adding Sharpness, Contrast, Saturation, Brightness, Hue effects. Big thanks to @Hans for this implementation. | 2c977a7
Added webcam and virtual cam features from Rope-Live fork. Thanks to @argenspin. | c0c7974

Improvements: 
Reset models and clear cuda cache when a user reloads parameters. | 0716aee
Updated requirements in order to support TensorRT-10.2.0. Activate the fallback to fp32 for TensorRT provider:wq because some models fail. | 3ebaed1

Changes:
Code Style. | 95f8acc
Removed TensorRT provider configuration if it is not used. | 2ed302c
Removed default TensorRT provider configuration. | 1269417
Delete invalid code. | 893026b

Bug Fixes:
Resolved an issue with the Face Scaling functionality by allowing scaling from the center. Thanks to @Doctor_Dentist . | 99bb44f
Fix for issue on Providers Priority setting that was not correctly restored at the system startup or during loading parameter functionality. Now Restorer switch and other settings will be not disabled during Providers Priority setting switching. | 8a35b3e
Temporary fix for “Enable Audio” option. Thanks to @argenspin and @coofly. | 2b34b79

Pearl v0.6.11 – 6.29
Contributors: @argenspin 

Features:
Add support for SimSwap 512 unofficial faceswapper model. | 9f701e4
Add support for GPEN 2048 restorer model. | 1dbaf0a
Add Face Likeness functionality. | 8175853
Add support for Ghost Face v1, Ghost Face v2, and Ghost Face v3. | 97f6a27
Add restore eyes and restore mouth functionalities. Big thanks to argenspin for this customization. | 8ed6b73
Added more face attributes  ['Neck','Eyebrows','Eyes','Nose','Lips','Mouth'] to the Face Parser. Also removed the previous Eyes and Mouth restoration using pixel blending. | 9948e1b
Added tensorrt exec. | 04e9895

Changes:
Code Style. | 1549c38
Changes to gitignore. | b3642f8

Bug Fixes:
Fix for an issue on selecting Face Swapper Model. | 124f92a
Fix for an issue when the current requested frame is not in the range of markers and parameters and parameters will always be applied. | 7f785a8
Fix for an issue regarding similarity in recognition function. | ff673f6

Pearl v0.6.7 - 6.8
Contributors: n/a

Features:
Add new functionality to allow the user to correct in real time the positions of detected 5 facial landmarks for all detected faces before passing them to recognizer and faceswapper models. | 3f12b07
Add Optimal similarity. It is a combination of many similarities, so the best one will be automatically selected depending basing on face alignment that is going to be processed. The environment will be ready when switching between Similarities without doing delete embedding and clear faces operations. | d4788f6

Bug Fixes:
Fix for an issue in showing landmarks when a video or image width,
height is less than 512 pixels..

Pearl v0.6.5
Contributors: @Corza 

Improvements:
Import Corza UberMod. | a93d442
Import Corza UberMod missing files. | 8b02b15

Changes:
Brought back the similarity of the face to the Opal version part 3. | d5af208

Bug Fixes:
Fixed the linux model problem. | a1c09e5
Brought back the similarity of the face to the Opal version part 2. | 17b2077
Fixed Linux compatibility. | f5a306d

Pearl v0.6.2
Contributors: n/a

Improvements:
Add support for 5-points Landmark detector.
Add Show Landmarks setting.

Changes:
Brought back the similarity of the face to the Opal version. | bd2516f

Bug Fixes:
Fix for issue that was causing incorrect detection of facial landmarks when the image processed by the 'Landmark' is smaller than the required size and from points setting was not enabled. | d814af7
Fix for issue when show landmarks setting is enabled and the incorrect keypoints value exceeds the image size. | 9872d10

Pearl v0.5.31
Contributors: n/a

dc11e43

Features:
Add support for from points in Landmarks Detectors. Using Face Detector keypoints, the image will be rotated before processing by Landmarks Detector.
Add support for GPEN 1024 restorer.

Improvements:
Improve Landmarks Detectors code.

Bug Fixes:
Fix issue regarding settings not automatically applied when changed.
Fix typo-error.
General bug fixing.

### [Discord](https://discord.gg/dzvpCUet)

### [Donate](https://www.paypal.com/donate/?business=XJX2E5ZTMZUSQ&no_recurring=0&item_name=Support+us+with+a+donation%21+Your+contribution+helps+us+continue+improving+and+providing+quality+content.+Thank+you%21&currency_code=EUR)

### [Wiki with install instructions and usage](N/A)

### [Demo Video (Rope-Next)](N/A)

### ${{\color{Goldenrod}{\textsf{Last Updated 2024-09-03}}}}$ ###
### ${{\color{Goldenrod}{\textsf{Welcome to Rope-Next!}}}}$ ###


![image](https://github.com/Hillobar/Rope/assets/63615199/40f7397f-713c-4813-ac86-bab36f6bd5ba)


Rope implements the insightface inswapper_128 model with a helpful GUI.
### [Discord](https://discord.gg/EcdVAFJzqp)

### [Donate](https://www.paypal.com/donate/?hosted_button_id=Y5SB9LSXFGRF2)

### [Wiki with install instructions and usage](https://github.com/Hillobar/Rope/wiki)

### [Demo Video (Rope-Ruby)](https://www.youtube.com/watch?v=4Y4U0TZ8cWY)

### ${{\color{Goldenrod}{\textsf{Last Updated 2024-05-27}}}}$ ###
### ${{\color{Goldenrod}{\textsf{Welcome to Rope-Pearl!}}}}$ ###

![Screenshot 2024-02-10 104718](https://github.com/Hillobar/Rope/assets/63615199/4b2ee574-c91e-4db2-ad66-5b775a049a6b)

### Updates for Rope-Pearl-00: ###
### To update from Opal-03a, just need to replace the rope folder.
* (feature) Selectable model swapping output resolution - 128, 256, 512
* (feature) Better selection of input images (ctrl and shift modifiers work mostly like windows behavior)
* (feature) Toggle between mean and median merging withou having to save to compare
* (feature) Added back keyboard controls (q, w, a, s, d, space)
* (feature) Gamma slider
* 
![image](https://github.com/Hillobar/Rope/assets/63615199/9d89fded-addb-46fe-b2d7-bfe6f1a88188)

### Performance:  ###
Machine: 3090Ti (24GB), i5-13600K

<img src="https://github.com/Hillobar/Rope/assets/63615199/3e3505db-bc76-48df-b8ac-1e7e86c8d751" width="200">

File: benchmark/target-1080p.mp4, 2048x1080, 269 frames, 25 fps, 10s

Rendering time in seconds (5 threads):

| Option | Crystal | Sapphire | Ruby | Opal | Pearl |
| --- | --- | --- | --- | --- | --- |
| Only Swap (128) | 7.3 | 7.5 | 4.4 | 4.3 | 4.4 |
| Swap (256) | --- | --- | --- | --- | 8.6 |
| Swap (512) | --- | --- | --- | --- | 28.6 |
| Swap+GFPGAN | 10.7 | 11.0 | 9.0 | 9.8 | 9.3 |
| Swap+Codeformer | 12.4 | 13.5 | 11.1 | 11.1 | 11.3 |
| Swap+one word CLIP | 10.4 | 11.2 | 9.1 | 9.3 | 9.3 |
| Swap+Occluder | 7.8 | 7.8 | 4.4 | 4.7 | 4.7 |
| Swap+MouthParser | 13.9 | 12.1 | 5.0 | 4.9 | 5.1 |

### Disclaimer: ###
Rope is a personal project that I'm making available to the community as a thank you for all of the contributors ahead of me.
I've copied the disclaimer from [Swap-Mukham](https://github.com/harisreedhar/Swap-Mukham) here since it is well-written and applies 100% to this repo.
 
I would like to emphasize that our swapping software is intended for responsible and ethical use only. I must stress that users are solely responsible for their actions when using our software.

Intended Usage: This software is designed to assist users in creating realistic and entertaining content, such as movies, visual effects, virtual reality experiences, and other creative applications. I encourage users to explore these possibilities within the boundaries of legality, ethical considerations, and respect for others' privacy.

Ethical Guidelines: Users are expected to adhere to a set of ethical guidelines when using our software. These guidelines include, but are not limited to:

Not creating or sharing content that could harm, defame, or harass individuals. Obtaining proper consent and permissions from individuals featured in the content before using their likeness. Avoiding the use of this technology for deceptive purposes, including misinformation or malicious intent. Respecting and abiding by applicable laws, regulations, and copyright restrictions.

Privacy and Consent: Users are responsible for ensuring that they have the necessary permissions and consents from individuals whose likeness they intend to use in their creations. We strongly discourage the creation of content without explicit consent, particularly if it involves non-consensual or private content. It is essential to respect the privacy and dignity of all individuals involved.

Legal Considerations: Users must understand and comply with all relevant local, regional, and international laws pertaining to this technology. This includes laws related to privacy, defamation, intellectual property rights, and other relevant legislation. Users should consult legal professionals if they have any doubts regarding the legal implications of their creations.

Liability and Responsibility: We, as the creators and providers of the deep fake software, cannot be held responsible for the actions or consequences resulting from the usage of our software. Users assume full liability and responsibility for any misuse, unintended effects, or abusive behavior associated with the content they create.

By using this software, users acknowledge that they have read, understood, and agreed to abide by the above guidelines and disclaimers. We strongly encourage users to approach this technology with caution, integrity, and respect for the well-being and rights of others.

Remember, technology should be used to empower and inspire, not to harm or deceive. Let's strive for ethical and responsible use of deep fake technology for the betterment of society.



  

import cv2

print("Opening native Windows Camera Driver settings...")
# We use CAP_DSHOW here specifically because it allows GUI access
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Change to 1 or 2 if needed

# This magic command forces Windows to open the raw hardware dialog
cap.set(cv2.CAP_PROP_SETTINGS, 1)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.imshow("Adjust Settings Here", cv2.resize(frame, (960, 540)))
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
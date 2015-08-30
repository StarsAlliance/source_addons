#ifndef _VUPMULTILANG_H_
#define _VUPMULTILANG_H_

typedef const char[60][2] VUPMULTISTRING;


VUPMULTISTRING VUP_MAIN_SUCCESS = "SUCCEEDED\n" , "����������\n";
VUPMULTISTRING VUP_MAIN_FAILED = "FAILED (Error:%u)\n" , "�� ����������(������:%u)\n";

VUPMULTISTRING VUP_MAIN_LOADINGIM = "Loading file %s into memory ...  " , "�������� ���� %s � ������ ... ";
VUPMULTISTRING VUP_MAIN_ANALYZEFF = "Analyzing file format ... " , "���������� ������ ����� ... ");
VUPMULTISTRING VUP_MAIN_UNKNOWNFF = "Unknown file format. Operation halted\n" , "����������� ������ �����.�������� ���������\n";
VUPMULTISTRING VUP_MAIN_DESTWIN32 = "Destination Operating System: Microsoft Windows\n" , "������� ��: �������(�.� �����)";
VUPMULTISTRING VUP_MAIN_DESTUNIX = "Destination Operating System: UNIX-Like Operating System\n" , "������� ��: UNIX �������� ������������ �������";
VUPMULTISTRING VUP_MAIN_TRYINGTODETECTGT = "Trying to detect game type from binary ...\n" , "������� ���������� ��� ���� �� �������� ������ ����� ...\n";
VUPMULTISTRING VUP_MAIN_SAVINGCHANGES = "Saving changes to destination file ... " , "�������� ��������� � ������� ���� ...";
VUPMULTISTRING VUP_MAIN_OPERATIONSCOMPLETED = "\nAll operations completed. Have fun!!!\n" , "\n ��� �������� ���������. ��������� ��� ����������������� ;)\n"

VUPMULTISTRING VUP_SHARED_FOUNDAT = "Found at" , "������� ��";
VUPMULTISTRING VUP_SHARED_NOTFOUND = "Not found" , "�� �������";
VUPMULTISTRING VUP_SHARED_PATCHING = "Patching ..." , "����������� ...";
VUPMULTISTRING VUP_SHARED_DONE = "Done" , "������";
VUPMULTISTRING VUP_SHARED_FAILED = "Failed" , "�� ����������";

VUPMULTISTRING VUP_ETQW_DETECTEDGT = "%s has been detected\n" , "��������� %s\n";


VUPMULTISTRING VUP_VLV_DETECTEDGT = "%s\nHas been detected\n" , "���������:\n%s\n";

#endif

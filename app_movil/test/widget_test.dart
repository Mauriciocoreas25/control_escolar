import 'package:flutter_test/flutter_test.dart';
import 'package:app_movil/main.dart';

void main() {
  testWidgets('SIGE Docente app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp(isLoggedIn: false));
    expect(find.text('SIGE Móvil'), findsOneWidget);
  });
}
